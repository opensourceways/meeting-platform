#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2024/8/16 14:11
# @Author  : Tom_zc
# @FileName: inner.py
# @Software: PyCharm
from rest_framework.authentication import BasicAuthentication
from rest_framework.filters import SearchFilter
from rest_framework.generics import CreateAPIView, DestroyAPIView, GenericAPIView, ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated

from meeting_platform.utils.customized.my_pagination import MyPagination
from meeting_platform.utils.customized.my_serializers import MySerializerParse, EmptySerializers
from meeting_platform.utils.ret_api import ret_json, capture_my_validation_exception, MyValidationError
from meeting_platform.utils.customized.my_view import MyRetrieveModelMixin, MyUpdateAPIView, MyListModelMixin
from meeting_platform.utils.operation_log import OperationLogModule, OperationLogDesc, OperationLogType, \
    logger_wrapper, set_log_thread_local, log_key

from meeting.application.meeting import MeetingApp
from meeting.controller.serializers.meeting_serializers import MeetingSerializer, \
    SingleMeetingSerializer
from meeting_platform.utils.ret_code import RetCode


class MeetingView(MySerializerParse, MyListModelMixin, ListAPIView, CreateAPIView):
    """create or list meeting"""
    serializer_class = MeetingSerializer
    authentication_classes = (BasicAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = MeetingApp.meeting_dao.get_queryset()
    filter_backends = [SearchFilter]
    search_fields = ['community', "mid", "id"]
    pagination_class = MyPagination
    app_class = MeetingApp()
    order_by = ["date", "create_time", "update_time"]
    order_type = ["asc", "desc"]

    @capture_my_validation_exception
    @logger_wrapper(OperationLogModule.OP_MODULE_MEETING, OperationLogType.OP_TYPE_CREATE,
                    OperationLogDesc.OP_DESC_MEETING_CREATE_CODE)
    def create(self, request, *args, **kwargs):
        """create meeting api"""
        set_log_thread_local(request, log_key, [request.data.get('community'), request.data.get('topic')])
        meeting = self.get_my_serializer_data(request)
        data = self.app_class.create(meeting)
        return ret_json(data=data)

    def get_queryset(self):
        """get the queryset"""
        order_by = self.request.query_params.get("order_by")
        if order_by and order_by not in self.order_by:
            raise MyValidationError(RetCode.STATUS_PARAMETER_ERROR)
        if not order_by:
            order_by = "date"
        order_type = self.request.query_params.get("order_type")
        if order_type and order_type not in self.order_type:
            raise MyValidationError(RetCode.STATUS_PARAMETER_ERROR)
        if not order_type:
            order_type = "desc"
        if order_type == "desc":
            order_by = "-{}".format(order_by)
        return self.queryset.order_by(order_by, 'start')


class SingleMeetingView(MySerializerParse, MyRetrieveModelMixin, MyUpdateAPIView, RetrieveAPIView, DestroyAPIView):
    """get or update or delete meeting"""
    lookup_field = "id"
    serializer_class = SingleMeetingSerializer
    queryset = MeetingApp.meeting_dao.get_queryset()
    authentication_classes = (BasicAuthentication,)
    permission_classes = (IsAuthenticated,)
    app_class = MeetingApp()

    @capture_my_validation_exception
    @logger_wrapper(OperationLogModule.OP_MODULE_MEETING, OperationLogType.OP_TYPE_MODIFY,
                    OperationLogDesc.OP_DESC_MEETING_UPDATE_CODE)
    def update(self, request, *args, **kwargs):
        """update meeting api"""
        set_log_thread_local(request, log_key, [request.data.get('community'),
                                                request.data.get('topic'), kwargs.get('id')])
        meeting = self.get_my_serializer_data(request)
        data = self.app_class.update(request, kwargs.get('id'), meeting)
        return ret_json(data=data)

    @capture_my_validation_exception
    @logger_wrapper(OperationLogModule.OP_MODULE_MEETING, OperationLogType.OP_TYPE_DELETE,
                    OperationLogDesc.OP_DESC_MEETING_DELETE_CODE)
    def destroy(self, request, *args, **kwargs):
        """delete meeting by mid"""
        set_log_thread_local(request, log_key, ["", "", kwargs.get('id')])
        data = self.app_class.delete(request, kwargs.get('id'))
        return ret_json(data=data)


class MeetingParticipantsView(RetrieveAPIView, GenericAPIView):
    lookup_field = "id"
    serializer_class = EmptySerializers
    queryset = MeetingApp.meeting_dao.get_queryset()
    authentication_classes = (BasicAuthentication,)
    app_class = MeetingApp()

    def retrieve(self, *args, **kwargs):
        data = self.app_class.get_participants(kwargs.get('id'))
        return ret_json(data=data)
