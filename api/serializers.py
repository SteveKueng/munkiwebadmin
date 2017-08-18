from rest_framework.serializers import Serializer, ModelSerializer

from reports.models import Machine, MunkiReport, ImagrReport

class MunkiReportDetailSerializer(ModelSerializer):
    class Meta:
        model = MunkiReport
        fields = [
            'timestamp',
            #'runtype',
            #'runstate',
            #'console_user',
            'errors',
            'warnings',
            'activity',
            'report',
        ]

class MachineListSerializer(ModelSerializer):
    class Meta:
        model = Machine
        fields = [
            'businessunit',
            'serial_number',
            'hostname',
            'os_version',
            'machine_model',
        ]

class MachineDetailSerializer(ModelSerializer):
    munkireport = MunkiReportDetailSerializer()
    class Meta:
        model = Machine
        fields = [
            'businessunit',
            'serial_number',
            'hostname',
            'username',
            'remote_ip',
            'machine_model',
            'cpu_type',
            'cpu_speed',
            'cpu_arch',
            'ram',
            'os_version',
            'current_status',
            'imagr_workflow',
            'simpleMDMID',
            'munkireport',
        ]
        #read_only_fields = ('munkireport',)
        depth = 1
