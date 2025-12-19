from rest_framework import serializers
from portal.models import rehabassistantsTbl,staffTbl,Farms

from .models import *
from rest_framework import serializers


class staffTblSerializer(serializers.ModelSerializer):

    class Meta:
        model = staffTbl
        # fields = '__all__'

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"



class rehabassistantsTblSerializer(serializers.ModelSerializer):
   
    po_first_name = serializers.ReadOnlyField(source='staffTbl_foreignkey.first_name')
    po_last_name = serializers.ReadOnlyField(source='staffTbl_foreignkey.last_name')
    district=serializers.ReadOnlyField(source='districtTbl_foreignkey.district')
    district_id=serializers.ReadOnlyField(source='districtTbl_foreignkey.id') 
    region_id=serializers.ReadOnlyField(source='districtTbl_foreignkey.reg_code.reg_code')
    region_name=serializers.ReadOnlyField(source='districtTbl_foreignkey.reg_code.region')
    rehab_code=serializers.ReadOnlyField(source='id')
    class Meta:
        model = rehabassistantsTbl
        # fields = '__all__'
        fields =("name","staff_code","phone_number","bank_branch","bank_account_number","gender","ssnit_number","momo_number","momo_account_name","dob","po_first_name","po_last_name","district","district_id","photo_staff","payment_option","designation","region_id","region_name","rehab_code")
        

class rehabassistantsTblSerializer(serializers.ModelSerializer):
   
    po_first_name = serializers.ReadOnlyField(source='staffTbl_foreignkey.first_name')
    po_last_name = serializers.ReadOnlyField(source='staffTbl_foreignkey.last_name')
    district=serializers.ReadOnlyField(source='districtTbl_foreignkey.district')
    district_id=serializers.ReadOnlyField(source='districtTbl_foreignkey.id') 
    region_id=serializers.ReadOnlyField(source='districtTbl_foreignkey.reg_code.reg_code')
    region_name=serializers.ReadOnlyField(source='districtTbl_foreignkey.reg_code.region')
    rehab_code=serializers.ReadOnlyField(source='id')
    class Meta:
        model = rehabassistantsTbl
        # fields = '__all__'
        fields =("name","staff_code","phone_number","bank_branch","bank_account_number","gender","ssnit_number","momo_number","momo_account_name","dob","po_first_name","po_last_name","district","district_id","photo_staff","payment_option","designation","region_id","region_name","rehab_code")



class Coco32FormCoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coco32FormCore
        fields = '__all__'

class Coco32FormWorkdoneByRaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coco32FormWorkdoneByRa
        fields = '__all__'

class Coco32FormWorkdoneByPoNspSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coco32FormWorkdoneByPoNsp
        fields = '__all__'


class WbpFarmsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Farms
        # fields = '__all__'
        fields =('geom','farm_id','farm_loc','farmer_nam','sex','age','id_number','name_ta','date','no_trees','coc_type',)




######################################################################################################################


# serializers.py
from rest_framework import serializers

class MobileLoginSerializer(serializers.Serializer):
    telephone = serializers.CharField(required=True, max_length=20)
    password = serializers.CharField(required=True, max_length=255)