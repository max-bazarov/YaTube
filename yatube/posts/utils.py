from django.core.paginator import Paginator


def get_paginator_page_obj(object_list, per_page, page_number):
    paginator = Paginator(object_list, per_page)
    return paginator.get_page(page_number)
