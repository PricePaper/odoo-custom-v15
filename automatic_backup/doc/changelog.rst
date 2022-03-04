`1.5.6 [2019-05-18]`
-------

- Rewrite part of the code. Removed calling tell() method because it is causing problems for some users.

`1.5.5 [2019-05-01]`
-------

- Fix issue with to small backups and dropbox

`1.5.4 [2019-01-06]`
-------

- Added support for big backups over Dropbox

`1.5.3 [2018-11-24]`
-------

- Removed decorator from dump_db method
- Added possibility to create backup with list_db = False option

`1.5.2 [2018-05-13]`
-------

- Use the same method for Google Drive database and filestore backups

`1.5.1 [2018-05-08]`
-------

- Fixed issue with Google Drive database only backup

`1.5.0 [2018-01-26]`
-------

- Added Amazon S3 backup option

`1.4.5 [2018-01-26]`
-------

- Fixed compatibility issue with Google Drive and Windows

`1.4.4 [2018-01-24]`
-------

- Fixed typo in code

`1.4.3 [2018-01-18]`
-------

- Changed name of the module

`1.4.2 [2017-12-16]`
-------

- Added support for custom Google Drive backup path

`1.4.1 [2017-12-01]`
-------

- Updated ir.model search to new version

`1.4.0 [2017-11-04]`
-------

- Added SFTP backup option

`1.3.1 [2017-10-29]`
-------

- Storing flow/auth files in Odoo filestore instead of database or Odoo folder

`1.3.0 [2017-10-15]`
-------

- Updated to Dropbox API v2

`1.2.5 [2017-10-15]`
-------

- Removed testing information

`1.2.4 [2017-07-27]`
-------

- Added testing information

`1.2.3 [2017-07-26]`
-------

- Specified required Dropbox python package version, compatibility issues with the newest one

`1.2.2 [2017-07-25]`
-------

- Fixed: Error with finding date of existing backups

`1.2.1 [2017-07-09]`
-------

- Fixed: writing args to other cron jobs

`1.2.0 [2017-05-28]`
-------

- Added Google Drive backup option

`1.1.8 [2017-05-23]`
-------

- Added option to change backup filename

`1.1.7 [2017-05-23]`
-------

- Fixed cron argument in Odoo 8

`1.1.6 [2017-05-18]`
-------

- Support for Dropbox Python Package v7.3.0

`1.1.5 [2017-05-11]`
-------

- Better filename validation

`1.1.4 [2017-05-10]`
-------

- Showing inactive backup rules

`1.1.3 [2017-05-10]`
-------

- Fixed bug with creating FTP backup on Windows

`1.1.2 [2017-05-09]`
-------

- Fixed bug with creating backup on Windows

`1.1.1 [2017-05-04]`
-------

- Windows-friendly backups

`1.1.0 [2017-05-03]`
-------

- Added Dropbox backup option

`1.0.1 [2017-05-01]`
-------

- Fixed bug - ignoring delete_old_backups False flag

`1.0.0 [2017-05-01]`
-------

- Initial release
