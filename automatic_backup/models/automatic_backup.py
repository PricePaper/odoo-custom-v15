# -*- coding: utf-8 -*-

import odoo
import ftplib
import os
import re
import pickle
import tempfile
import base64
import shutil
import json
import requests

from os import listdir
from os.path import isfile, join
from odoo import fields, models, api, exceptions
from odoo.tools.translate import _
from datetime import datetime
from datetime import date, timedelta
from odoo.tools import config
from werkzeug import urls

backup_pattern = '.*_\d\d\d\d-\d\d-\d\d \d\d_\d\d_\d\d.(zip|dump)$'

no_dropbox = False
try:
    import dropbox
except ImportError:
    no_dropbox = True

except ImportError:
    no_pydrive = True

no_pysftp = False
try:
    import pysftp
except ImportError:
    no_pysftp = True

no_boto3 = False
try:
    import boto3
except ImportError:
    no_boto3 = True


class AutomaticBackup(models.Model):

    _name = 'automatic.backup'
    _description = 'Automatic Backup'
    _inherit = ['mail.thread']

    name = fields.Char(default='Automatic Backup')
    automatic_backup_rule_ids = fields.One2many('ir.cron', 'automatic_backup_id', string='Automatic Backup Rule')
    successful_backup_notify_emails = fields.Char(string='Successful Backup Notification')
    failed_backup_notify_emails = fields.Char(string='Failed Backup Notification')
    delete_old_backups = fields.Boolean(default=False)

    # odoo server settings
    limit_time_cpu = fields.Integer(string='Maximum allowed CPU time per request (in seconds)',
                                    compute='compute_odoo_settings', inverse='set_odoo_settings')
    limit_time_real = fields.Integer(string='Maximum allowed Real time per request (in seconds)',
                                     compute='compute_odoo_settings', inverse='set_odoo_settings')
    limit_time_real_cron = fields.Integer(
        string='Maximum allowed Real time per cron job (in seconds / Set to 0 for no limit)',
        compute='compute_odoo_settings', inverse='set_odoo_settings')

    # google drive settings
    google_drive_client_id = fields.Char(required=1, default='598905559630.apps.googleusercontent.com')
    google_drive_client_secret = fields.Char(required=1, default='vTmou73c-njP-1qCxm7qx7QE')
    google_drive_redirect_uri = fields.Char(required=1, default='urn:ietf:wg:oauth:2.0:oob')
    google_drive_scopes = fields.Char(required=1, default='https://www.googleapis.com/auth/drive https://www.googleapis.com/auth/drive.file')
    google_drive_uri = fields.Char(compute='compute_google_drive_uri', store=False)
    google_drive_authorization_code = fields.Char()
    google_drive_refresh_token = fields.Char()
    google_drive_access_token = fields.Char()
    google_drive_access_token_expire_date = fields.Datetime()

    def compute_odoo_settings(self):
        self.limit_time_cpu = config['limit_time_cpu']
        self.limit_time_real = config['limit_time_real']
        self.limit_time_real_cron = config['limit_time_real_cron']

    def set_odoo_settings(self):
        config['limit_time_cpu'] = self.limit_time_cpu
        config['limit_time_real'] = self.limit_time_real
        config['limit_time_real_cron'] = self.limit_time_real_cron
        config.save()

    @api.depends('google_drive_scopes', 'google_drive_redirect_uri', 'google_drive_client_id')
    def compute_google_drive_uri(self):
        encoded_params = urls.url_encode({
            'scope': self.google_drive_scopes,
            'redirect_uri': self.google_drive_redirect_uri,
            'client_id': self.google_drive_client_id,
            'response_type': 'code',
        })
        self.google_drive_uri = '%s?%s' % ('https://accounts.google.com/o/oauth2/auth', encoded_params)

    @api.onchange('google_drive_authorization_code')
    def constrains_google_drive_authorization_code(self):
        if not self.google_drive_authorization_code:
            return
        headers = {"Content-type": "application/x-www-form-urlencoded"}
        data = {
            'code': self.google_drive_authorization_code,
            'client_id': self.google_drive_client_id,
            'client_secret': self.google_drive_client_secret,
            'redirect_uri': self.google_drive_redirect_uri,
            'grant_type': 'authorization_code',
        }
        req = requests.post('https://accounts.google.com/o/oauth2/token', data=data, headers=headers, timeout=60)
        req.raise_for_status()
        response = req.json()
        self.google_drive_refresh_token = response['refresh_token']
        self.google_drive_access_token = response['access_token']
        self.google_drive_access_token_expire_date = datetime.now() + timedelta(seconds=response['expires_in'])

    def google_drive_refresh_access_token(self):
        data = {
            'client_id': self.google_drive_client_id,
            'refresh_token': self.google_drive_refresh_token,
            'client_secret': self.google_drive_client_secret,
            'grant_type': 'refresh_token',
            'scope': self.google_drive_scopes,
        }
        headers = {"Content-type": "application/x-www-form-urlencoded"}
        req = requests.post('https://accounts.google.com/o/oauth2/token', data=data, headers=headers, timeout=60)
        req.raise_for_status()
        self.google_drive_access_token = req.json().get('access_token')

    def default_filename(self):
        return self.env.cr.dbname

    filename = fields.Char(default=default_filename)


    @api.constrains('delete_days')
    def constrains_delete_days(self):
        for record in self:
            if record.delete_old_backups:
                if record.delete_days is False or record.delete_days < 1:
                    raise exceptions.ValidationError(_('Minimal Delete Days = 1'))

    delete_days = fields.Integer(string='Delete backups older than [days]', default=30)


def dump_db_manifest(cr):
    pg_version = "%d.%d" % divmod(cr._obj.connection.server_version / 100, 100)
    cr.execute("SELECT name, latest_version FROM ir_module_module WHERE state = 'installed'")
    modules = dict(cr.fetchall())
    manifest = {
        'odoo_dump': '1',
        'db_name': cr.dbname,
        'version': odoo.release.version,
        'version_info': odoo.release.version_info,
        'major_version': odoo.release.major_version,
        'pg_version': pg_version,
        'modules': modules,
    }
    return manifest


def dump_db(db_name, stream, backup_format='zip'):
    cmd = ['pg_dump', '--no-owner']
    cmd.append(db_name)
    if backup_format == 'zip':
        with odoo.tools.osutil.tempdir() as dump_dir:
            filestore = odoo.tools.config.filestore(db_name)
            if os.path.exists(filestore):
                shutil.copytree(filestore, os.path.join(dump_dir, 'filestore'))
            with open(os.path.join(dump_dir, 'manifest.json'), 'w') as fh:
                db = odoo.sql_db.db_connect(db_name)
                with db.cursor() as cr:
                    json.dump(dump_db_manifest(cr), fh, indent=4)
            cmd.insert(-1, '--file=' + os.path.join(dump_dir, 'dump.sql'))
            odoo.tools.exec_pg_command(*cmd)
            if stream:
                odoo.tools.osutil.zip_dir(dump_dir, stream, include_dir=False, fnct_sort=lambda file_name: file_name != 'dump.sql')
            else:
                t=tempfile.TemporaryFile()
                odoo.tools.osutil.zip_dir(dump_dir, t, include_dir=False, fnct_sort=lambda file_name: file_name != 'dump.sql')
                t.seek(0)
                return t
    else:
        cmd.insert(-1, '--format=c')
        stdin, stdout = odoo.tools.exec_pg_command_pipe(*cmd)
        if stream:
            shutil.copyfileobj(stdout, stream)
        else:
            return stdout


odoo.service.db.dump_db = dump_db


class Cron(models.Model):

    _inherit = 'ir.cron'

    @api.model
    def create(self, vals):
        if 'dropbox_authorize_url_rel' in vals:
            vals['dropbox_authorize_url'] = vals['dropbox_authorize_url_rel']
        if 'backup_type' in vals:
            vals['name'] = 'Backup ' + vals['backup_type'] + ' ' + vals['backup_destination']
            vals['numbercall'] = -1
            vals['state'] = 'code'
            vals['code'] = ''
            vals['model_id'] = self.env['ir.model'].search([('model', '=', 'ir.cron')]).id
        output = super(Cron, self).create(vals)
        if 'backup_type' in vals:
            output.code = 'env[\'ir.cron\'].database_backup_cron_action(' + str(output.id) + ')'
        return output


    def write(self, vals):
        for rec in self:
            if 'dropbox_authorize_url_rel' in vals:
                vals['dropbox_authorize_url'] = vals['dropbox_authorize_url_rel']
        return super(Cron, self).write(vals)


    def unlink(self):
        # delete flow/auth files
        for rec in self:
            self.env['ir.attachment'].browse(rec.dropbox_flow).unlink()
        output = super(Cron, self).unlink()
        return output

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        if 'backup_rule' in self.env.context:
            args += ['|', ('active', '=', True), ('active', '=', False)]
        return super(Cron, self).search(args, offset, limit, order, count=count)


    @api.constrains('backup_type', 'backup_destination')
    def create_name(self):
        for rec in self:
            rec.name = 'Backup ' + rec.backup_type + ' ' + rec.backup_destination

    @api.onchange('backup_destination')
    def onchange_backup_destination(self):
        if self.backup_destination == 'ftp':
            self.ftp_port = 21

        if self.backup_destination == 'sftp':
            self.ftp_port = 22
            if no_pysftp:
                raise exceptions.Warning(_('Missing required pysftp python package\n'
                                           'https://pypi.python.org/pypi/pysftp'))

        if self.backup_destination == 'dropbox':
            if no_dropbox:
                raise exceptions.Warning(_('Missing required dropbox python package\n'
                                           'https://pypi.python.org/pypi/dropbox'))
            flow = dropbox.DropboxOAuth2FlowNoRedirect('jqurrm8ot7hmvzh', '7u0goz5nmkgr1ot')
            self.dropbox_authorize_url = flow.start()
            self.dropbox_authorize_url_rel = self.dropbox_authorize_url

            self.dropbox_flow = self.env['ir.attachment'].create(dict(
                datas=base64.b64encode(pickle.dumps(flow)),
                name='dropbox_flow',
                store_fname='dropbox_flow',
                description='Automatic Backup File'
            )).id

        if self.backup_destination == 'google_drive':
            if not self.automatic_backup_id.google_drive_access_token:
                raise exceptions.ValidationError(_('Please set up Google Drive Authorization Code!'))


    @api.constrains('backup_destination', 'dropbox_authorization_code', 'dropbox_flow')
    def constrains_dropbox(self):
          for record in self:
            if record.backup_destination == 'sftp':
                if no_pysftp:
                    raise exceptions.Warning(_('Missing required pysftp python package\n'
                                               'https://pypi.python.org/pypi/pysftp'))

            if record.backup_destination == 'dropbox':
                if no_dropbox:
                    raise exceptions.Warning(_('Missing required dropbox python package\n'
                                               'https://pypi.python.org/pypi/dropbox'))

                ia = self.env['ir.attachment'].browse(record.dropbox_flow)
                ia.res_model = 'ir.cron'
                ia.res_id = record.id

                flow = pickle.loads(base64.b64decode(ia.datas))
                result = flow.finish(record.dropbox_authorization_code.strip())
                record.dropbox_access_token = result.access_token
                record.dropbox_user_id = result.user_id

            if record.backup_destination == 's3':
                if no_boto3:
                    raise exceptions.Warning(_('Missing required boto3 python package\n'
                                               'https://pypi.python.org/pypi/boto3'))


    def check_settings(self):
        for rec in self:
            res = rec.create_backup(True)
            return {
                'name': 'Success',
                'type': 'ir.actions.act_window',
                'res_model': 'check.settings',
                'view_mode': 'form',
                'view_type': 'form',
                'target': 'new',
            }


    def backup_btn(self):
        for backup in self:
            backup.create_backup()

    def get_selection_field_value(self, field, key):
        my_model_obj = self
        return dict(my_model_obj.fields_get(allfields=[field])[field]['selection'])[key]


    def show_rule_form(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Backup Rule',
            'res_model': 'ir.cron',
            'res_id': self.id,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
        }

    def create_backup(self, check=False):
        filename = ''
        if check is False:
            backup_binary = odoo.service.db.dump_db(self.env.cr.dbname, None, self.backup_type)
        else:
            backup_binary = tempfile.TemporaryFile()
            backup_binary.write(str.encode('Dummy File'))
            backup_binary.seek(0)
        backup_size = os.stat(backup_binary.name).st_size

        # delete unused flow/auth files
        self.env['ir.attachment'].search([('description', '=', 'Automatic Backup File'), ('res_id', '=', False)]).unlink()

        if self.backup_destination == 'folder':
            filename = self.folder_path + os.sep + self.automatic_backup_id.filename + '_' + \
                       str(datetime.now()).split('.')[0].replace(':', '_') + '.' + self.backup_type
            file_ = open(filename, 'wb')
            while True:
                tmp_data = backup_binary.read(1024)
                if not tmp_data:
                    break
                file_.write(tmp_data)
            file_.close()
            if check is True:
                os.remove(filename)
            if self.automatic_backup_id.delete_old_backups:
                files = [f for f in listdir(self.folder_path) if isfile(join(self.folder_path, f))]
                for backup in files:
                    if re.match(backup_pattern, backup) is not None:
                        px = len(backup) - 24
                        if backup.endswith('.dump'):
                            px -= 1
                        filedate = date(int(backup[px+1:px+5]), int(backup[px+6:px+8]), int(backup[px+9:px+11]))
                        if filedate + timedelta(days=self.automatic_backup_id.delete_days) < date.today():
                            os.remove(self.folder_path + os.sep + backup)
                            self.file_delete_message(backup)

        if self.backup_destination == 'ftp':
            filename = self.automatic_backup_id.filename + '_' + str(datetime.now()).split('.')[0].replace(':', '_') \
                       + '.' + self.backup_type
            ftp = ftplib.FTP()
            ftp.connect(self.ftp_address, self.ftp_port)
            ftp.login(self.ftp_login, self.ftp_password)
            ftp.cwd(self.ftp_path)
            ftp.storbinary('STOR ' + filename, backup_binary)
            if check is True:
                ftp.delete(filename)
            if self.automatic_backup_id.delete_old_backups:
                for backup in ftp.nlst():
                    if re.match(backup_pattern, backup) is not None:
                        px = len(backup) - 24
                        if backup.endswith('.dump'):
                            px -= 1
                        filedate = date(int(backup[px + 1:px + 5]), int(backup[px + 6:px + 8]), int(backup[px + 9:px + 11]))
                        if filedate + timedelta(days=self.automatic_backup_id.delete_days) < date.today():
                            ftp.delete(backup)
                            self.file_delete_message(backup)

        if self.backup_destination == 'sftp':
            filename = self.automatic_backup_id.filename + '_' + str(datetime.now()).split('.')[0].replace(':', '_') \
                       + '.' + self.backup_type

            cnopts = pysftp.CnOpts()
            cnopts.hostkeys = None
            sftp = pysftp.Connection(self.ftp_address, username=self.ftp_login, password=self.ftp_password,
                                     cnopts=cnopts, port=self.ftp_port)
            sftp.putfo(backup_binary, self.ftp_path + '/' + filename)
            if check is True:
                sftp.remove(self.ftp_path + '/' + filename)
            if self.automatic_backup_id.delete_old_backups:
                for backup in sftp.listdir(self.ftp_path):
                    if re.match(backup_pattern, backup) is not None:
                        px = len(backup) - 24
                        if backup.endswith('.dump'):
                            px -= 1
                        filedate = date(int(backup[px + 1:px + 5]), int(backup[px + 6:px + 8]),
                                        int(backup[px + 9:px + 11]))
                        if filedate + timedelta(days=self.automatic_backup_id.delete_days) < date.today():
                            sftp.remove(self.ftp_path + '/' + backup)
                            self.file_delete_message(backup)

        if self.backup_destination == 'dropbox':
            filename = self.automatic_backup_id.filename + '_' + str(datetime.now()).split('.')[0].replace(':', '_') \
                       + '.' + self.backup_type
            client = dropbox.Dropbox(self.dropbox_access_token)

            # 64mb chunk
            CHUNK_SIZE = 67108864

            file_chunk_data = backup_binary.read(CHUNK_SIZE)
            offset = len(file_chunk_data)
            upload_session_start_result = client.files_upload_session_start(file_chunk_data)
            cursor = dropbox.files.UploadSessionCursor(session_id=upload_session_start_result.session_id,
                                                       offset=offset)
            commit = dropbox.files.CommitInfo(path='/' + filename)

            if backup_size <= CHUNK_SIZE:
                CHUNK_SIZE = int(backup_size * 0.6)
            while True:
                if (backup_size - offset) <= CHUNK_SIZE:
                    client.files_upload_session_finish(backup_binary.read(CHUNK_SIZE), cursor, commit)
                    break
                else:
                    file_chunk_data = backup_binary.read(CHUNK_SIZE)
                    offset += len(file_chunk_data)
                    client.files_upload_session_append(file_chunk_data, cursor.session_id, cursor.offset)
                    cursor.offset = offset

            if check is True:
                client.files_delete_v2('/' + filename)
            if self.automatic_backup_id.delete_old_backups:
                for f in client.files_list_folder('').entries:
                    if re.match(backup_pattern, f.name) is not None:
                        px = len(f.name) - 24
                        if f.name.endswith('.dump'):
                            px -= 1
                        filedate = date(int(f.name[px + 1:px + 5]), int(f.name[px + 6:px + 8]), int(f.name[px + 9:px + 11]))
                        if filedate + timedelta(days=self.automatic_backup_id.delete_days) < date.today():
                            client.files_delete_v2('/' + f.name)
                            self.file_delete_message(f.name[1:])

        if self.backup_destination == 'google_drive':
            if not self.automatic_backup_id.google_drive_access_token:
                return
            self.automatic_backup_id.google_drive_refresh_access_token()
            filename = self.automatic_backup_id.filename + '_' + \
                       str(datetime.now()).split('.')[0].replace(':', '_') + '.' + self.backup_type

            auth_header = {
                "Authorization": "Bearer " + self.automatic_backup_id.google_drive_access_token,
            }

            encoded_params = urls.url_encode({
                'scope': 'drive',
                'q': "mimeType = 'application/vnd.google-apps.folder' and name = 'Odoo Backups'",
                'fields': 'nextPageToken, files(id, name)',
                'pageToken': None,
            })
            response = requests.get('https://www.googleapis.com/drive/v3/files?' + encoded_params,
                                    headers=auth_header).json()
            folder_id = False
            for folder in response.get('files', dict()):
                folder_id = folder['id']
                break
            if not folder_id:
                params = dict(
                    uploadType='multipart',
                    name='Odoo Backups',
                    mimeType='application/vnd.google-apps.folder',
                )
                response = requests.post('https://www.googleapis.com/drive/v3/files', headers=auth_header,
                                         json=params).json()
                folder_id = response['id']

            mimetype = 'application/zip' if (self.backup_type == 'zip') else 'application/octet-stream'
            params = {
                "name": filename,
                "mimeType": mimetype,
                "parents": [folder_id],
            }
            r = requests.post(
                "https://www.googleapis.com/upload/drive/v3/files?uploadType=resumable",
                headers=auth_header,
                json=params,
            )
            location = r.headers['Location']
            headers = {"Content-Range": "bytes 0-" + str(backup_size - 1) + "/" + str(backup_size)}
            r = requests.put(
                location,
                headers=headers,
                data=backup_binary,
            )

            if self.automatic_backup_id.delete_old_backups:
                encoded_params = urls.url_encode({
                    'scope': 'drive',
                    'q': "'%s' in parents and modifiedTime < '%s'" % (
                        folder_id, str((datetime.now() - timedelta(days=self.automatic_backup_id.delete_days)).date())),
                })
                response = requests.get('https://www.googleapis.com/drive/v3/files?' + encoded_params,
                                        headers=auth_header).json()
                for file in response['files']:
                    requests.delete('https://www.googleapis.com/drive/v3/files/' + file['id'], headers=auth_header)

            if check:
                delete_id = r.json()['id']
                requests.delete('https://www.googleapis.com/drive/v3/files/' + delete_id, headers=auth_header)

        if self.backup_destination == 's3':
            filename = self.automatic_backup_id.filename + '_' + str(datetime.now()).split('.')[0].replace(':', '_') \
                       + '.' + self.backup_type
            s3 = boto3.resource('s3', aws_access_key_id=self.s3_access_key, aws_secret_access_key=self.s3_access_key_secret)
            s3.Bucket(self.s3_bucket_name).put_object(Key='Odoo Automatic Backup/' + filename, Body=backup_binary)
            if self.automatic_backup_id.delete_old_backups:
                for o in s3.Bucket(self.s3_bucket_name).objects.all():
                    if o.key.startswith('Odoo Automatic Backup/'):
                        px = len(o.key) - 24
                        if o.key.endswith('.dump'):
                            px -= 1
                        filedate = date(int(o.key[px + 1:px + 5]), int(o.key[px + 6:px + 8]), int(o.key[px + 9:px + 11]))
                        if filedate + timedelta(days=self.automatic_backup_id.delete_days) < date.today():
                            self.file_delete_message(o.key)
                            o.delete()

        backup_binary.close()
        # if check is True:
        #     return {
        #         'name': 'Success',
        #         'type': 'ir.actions.act_window',
        #         'res_model': '',
        #         'view_mode': 'form',
        #         'view_type': 'form',
        #         'target': 'new',
        #     }
            #raise exceptions.Warning(_('Settings are correct.'))
        self.success_message(filename)

    def success_message(self, filename):
        msg = _('Backup created successfully!') + '<br/>'
        msg += _('Backup Type: ') + self.get_selection_field_value('backup_type', self.backup_type) + '<br/>'
        msg += _('Backup Destination: ') + self.get_selection_field_value('backup_destination',
                                                                          self.backup_destination) + '<br/>'
        if self.backup_destination == 'folder':
            msg += _('Folder Path: ') + self.folder_path + '<br/>'
        if self.backup_destination == 'ftp':
            msg += _('FTP Adress: ') + self.ftp_address + '<br/>'
            msg += _('FTP Path: ') + self.ftp_path + '<br/>'
        msg += _('Filename: ') + filename + '<br/>'
        self.env['mail.message'].create(dict(
            subject=_('Backup created successfully!'),
            body=msg,
            email_from=self.env['res.users'].browse(self.env.uid).email,
            model='automatic.backup',
            res_id=self.automatic_backup_id.id,
        ))
        if self.automatic_backup_id.successful_backup_notify_emails:
            self.env['mail.mail'].create(dict(
                subject=_('Backup created successfully!'),
                body_html=msg,
                email_from=self.env['res.users'].browse(self.env.uid).email,
                email_to=self.automatic_backup_id.successful_backup_notify_emails,
            )).send()

    def file_delete_message(self, filename):
        msg = _('Old backup deleted!') + '<br/>'
        msg += _('Backup Type: ') + self.get_selection_field_value('backup_type', self.backup_type) + '<br/>'
        msg += _('Backup Destination: ') + self.get_selection_field_value('backup_destination',
                                                                          self.backup_destination) + '<br/>'
        if self.backup_destination == 'folder':
            msg += _('Folder Path: ') + self.folder_path + '<br/>'
        if self.backup_destination == 'ftp':
            msg += _('FTP Adress: ') + self.ftp_address + '<br/>'
            msg += _('FTP Path: ') + self.ftp_path + '<br/>'
        msg += _('Filename: ') + filename + '<br/>'
        self.env['mail.message'].create(dict(
            subject=_('Old backup deleted!'),
            body=msg,
            email_from=self.env['res.users'].browse(self.env.uid).email,
            model='automatic.backup',
            res_id=self.automatic_backup_id.id,
        ))
        if self.automatic_backup_id.successful_backup_notify_emails:
            self.env['mail.mail'].create(dict(
                subject=_('Old backup deleted!'),
                body_html=msg,
                email_from=self.env['res.users'].browse(self.env.uid).email,
                email_to=self.automatic_backup_id.successful_backup_notify_emails,
            )).send()

    @api.model
    def database_backup_cron_action(self, *args):
        backup_rule = False
        try:
            if len(args) != 1 or isinstance(args[0], int) is False:
                raise exceptions.ValidationError(_('Wrong method parameters'))
            rule_id = args[0]
            backup_rule = self.browse(rule_id)
            backup_rule.create_backup()
        except Exception as e:
            msg = _('Automatic backup failed!') + '<br/>'
            msg += _('Backup Type: ') + backup_rule.get_selection_field_value('backup_type', backup_rule.backup_type) + '<br/>'
            msg += _('Backup Destination: ') + backup_rule.get_selection_field_value('backup_destination', backup_rule.backup_destination) + '<br/>'
            if backup_rule.backup_destination == 'folder':
                msg += _('Folder Path: ') + backup_rule.folder_path + '<br/>'
            if backup_rule.backup_destination == 'ftp':
                msg += _('FTP Adress: ') + backup_rule.ftp_address + '<br/>'
                msg += _('FTP Path: ') + backup_rule.ftp_path + '<br/>'
            msg += _('Exception: ') + str(e) + '<br/>'
            self.env['mail.message'].create(dict(
                subject=_('Automatic backup failed!'),
                body=msg,
                email_from=self.env['res.users'].browse(self.env.uid).email,
                model='automatic.backup',
                res_id=backup_rule.automatic_backup_id.id,
            ))
            if backup_rule.automatic_backup_id.failed_backup_notify_emails:
                self.env['mail.mail'].create(dict(
                    subject=_('Automatic backup failed!'),
                    body_html=msg,
                    email_from=self.env['res.users'].browse(self.env.uid).email,
                    email_to=backup_rule.automatic_backup_id.failed_backup_notify_emails,
                )).send()

    automatic_backup_id = fields.Many2one('automatic.backup')
    backup_type = fields.Selection([('dump', 'Database Only'),
                                    ('zip', 'Database and Filestore')],
                                   string='Backup Type')
    backup_destination = fields.Selection([('folder', 'Folder'),
                                           ('ftp', 'FTP'),
                                           ('sftp', 'SFTP'),
                                           ('dropbox', 'Dropbox'),
                                           ('google_drive', 'Google Drive'),
                                           ('s3', 'Amazon S3')],
                                          string='Backup Destionation')
    folder_path = fields.Char(string='Folder Path')
    ftp_address = fields.Char(string='URL')
    ftp_port = fields.Integer(string='Port')
    ftp_login = fields.Char(string='Login')
    ftp_password = fields.Char(string='Password')
    ftp_path = fields.Char(string='Path')
    dropbox_authorize_url = fields.Char(string='Authorize URL')
    dropbox_authorize_url_rel = fields.Char()
    dropbox_authorization_code = fields.Char(string='Authorization Code')
    dropbox_flow = fields.Integer()
    dropbox_access_token = fields.Char()
    dropbox_user_id = fields.Char()
    dropbox_path = fields.Char(default='/Odoo Automatic Backups/', string='Backup Path')
    s3_bucket_name = fields.Char(string='Bucket name')
    s3_username = fields.Char(string='Username')
    s3_access_key = fields.Char(string='Access key')
    s3_access_key_secret = fields.Char(string='Acces key secret')
