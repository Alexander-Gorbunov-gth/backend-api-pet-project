from django.core.exceptions import ObjectDoesNotExist

from rest_framework import serializers


class NotNullVAlidator:
    requires_context = True

    def __call__(self, value, serializer_field):
        if not value:
            raise serializers.ValidationError(
                f"{serializer_field.label} не может быть пустым"
            )


class RecipeValidator:

    def __init__(self):
        pass

    def _obj_is_empty(self, objs, name):
        if not objs:
            raise serializers.ValidationError({name: f"{name} не переданы"})

    def _obj_does_not_exist(self, model, obj_item, name):
        try:
            return model.objects.get(id=obj_item)
        except ObjectDoesNotExist:
            raise serializers.ValidationError({name: f"{name} не найден"})

    def tag_validation(self, model, objs):
        self._obj_is_empty(objs, "tag")
        obj_list = []
        for obj_item in objs:
            obj = self._obj_does_not_exist(model, obj_item, "tag")
            if obj in obj_list:
                raise serializers.ValidationError({"tags": "Тэги одинаковы"})
            obj_list.append(obj)

    def ingredient_validation(self, model, objs):
        self._obj_is_empty(objs, "ingredient")
        obj_list = []
        for obj_item in objs:
            obj_item_id = obj_item.get("id")
            obj = self._obj_does_not_exist(model, obj_item_id, "ingredient")
            if obj in obj_list:
                raise serializers.ValidationError(
                    {"ingredient": "Ингридиенты одинаковы"}
                )
            obj_list.append(obj)
            if int(obj_item["amount"]) <= 0:
                raise serializers.ValidationError(
                    {"ingredients": f"Слишком мало {obj.name}"}
                )
