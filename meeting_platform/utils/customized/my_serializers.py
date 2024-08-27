# -*- coding: utf-8 -*-
# @Time    : 2024/6/17 18:44
# @Author  : Tom_zc
# @FileName: my_serializers.py
# @Software: PyCharm

from rest_framework.serializers import Serializer


# noinspection PyAbstractClass
class EmptySerializers(Serializer):
    """Nothing to do in EmptySerializers"""
    pass


# noinspection PyUnresolvedReferences
class MySerializerParse:
    def get_my_serializer_data(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data
