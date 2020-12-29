# -*- coding: utf-8 -*-

from odoo.tools import float_round


def get_margin(sell, cost, percent=False):
    """Helper function to calculate margin. If percent=True, we return the float * 100"""
    try:
        margin = (sell - cost) / sell
    except ZeroDivisionError:
        margin = -.99999

    if percent:
        margin *= 100

    return float_round(margin, precision_digits=2)


def get_price(cost, margin, percent=False):
    """Helper function to calculate a price using margin. If percent=True, we return the float * 100"""
    if percent:
        margin /= 100.0

    try:
        price = cost / (1 - margin)
    except ZeroDivisionError:
        price = cost / .00001

    return float_round(cost / (1 - margin), precision_digits=2)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
