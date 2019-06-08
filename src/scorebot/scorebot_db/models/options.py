#!/usr/bin/python3
# Scorebot UDP (Universal Development Platform)
#
# The Scorebot Project / iDigitalFlame 2019

from scorebot_utils import invalidate_cache
from scorebot_utils.restful import HttpError428
from django.db.models import (
    Model,
    CharField,
    AutoField,
    OneToOneField,
    ForeignKey,
    BooleanField,
    CASCADE,
    ObjectDoesNotExist,
)


class Option(Model):
    class Meta:
        db_table = "options"
        verbose_name = "Game Option"
        verbose_name_plural = "Game Options"

    __parents__ = [("game", "Game")]

    ID = AutoField(
        db_column="id",
        verbose_name="Option ID",
        null=False,
        primary_key=True,
        editable=False,
    )
    Name = CharField(
        db_column="name", verbose_name="Option Name", null=False, max_length=255
    )

    def __str__(self):
        return "%s (%d settings)" % (self.Name, self.Keys.all().count())

    def rest_json(self):
        k = self.Keys.all()
        r = {"id": self.ID, "name": self.Name}
        if len(k) > 0:
            r["keys"] = [i.rest_json() for i in k]
        return r

    def contains(self, name):
        try:
            self.Keys.all().get(Name__iexact=name)
        except ObjectDoesNotExist:
            return False
        return True

    def set(self, name, value):
        k = OptionKey()
        try:
            k = self.Keys.all().get(Name__iexact=name)
        except ObjectDoesNotExist:
            k.Name = name
            k.Option = self
        self.save()
        k.save()
        v = OptionValue()
        if isinstance(value, int):
            v.Value = "%d" % value
            v.Number = True
        else:
            v.Value = value
        v.Key = k
        v.save()
        return value

    def save(self, *args, **kwargs):
        for g in self.Game.all():
            invalidate_cache(g.ID)
        return super().save(*args, **kwargs)

    def rest_put(self, parent, data):
        if "name" not in data:
            return HttpError428("options name")
        self.Name = data["name"]
        self.save()
        if parent is not None:
            parent.Options = self
            parent.save()
        return self.rest_json()

    def get(self, name, default=None):
        try:
            k = self.Keys.all().get(Name__iexact=name)
            if hasattr(k, "Value"):
                if k.Value.Number:
                    try:
                        return int(k.Value.Value)
                    except ValueError:
                        pass
                return k.Value.Value
        except ObjectDoesNotExist:
            pass
        return default

    def rest_delete(self, parent, name):
        if name is None:
            self.save()
            self.delete()
        return None

    def rest_post(self, parent, name, data):
        if parent is not None:
            parent.Options = self
            parent.save()
        if name is None and "name" in data:
            self.Name = data["name"]
        elif name == "name":
            self.Name = data
        self.save()
        return self.rest_json()


class OptionKey(Model):
    class Meta:
        db_table = "option_keys"
        verbose_name = "Option Key"
        verbose_name_plural = "Option Keys"

    __parents__ = [("option", "Option")]

    ID = AutoField(
        db_column="id",
        verbose_name="Option Key ID",
        null=False,
        primary_key=True,
        editable=False,
    )
    Name = CharField(
        db_column="name", verbose_name="Option Key Name", null=False, max_length=255
    )
    Option = ForeignKey(
        db_column="option",
        verbose_name="Option Key Parent",
        null=False,
        on_delete=CASCADE,
        to="scorebot_db.Option",
        related_name="Keys",
    )

    def __str__(self):
        if hasattr(self, "Value"):
            return "Key '%s' = %s" % (self.fullname(), self.Value.value())
        return "Key '%s'" % self.fullname()

    def fullname(self):
        if self.Option is None:
            return self.Name
        return "%s\%s" % (self.Option.Name, self.Name)

    def rest_json(self):
        if hasattr(self, "Value"):
            return {
                "id": self.ID,
                "name": self.Name,
                "option": self.Option.ID,
                "value": self.Value.Value,
                "value_id": self.Value.ID,
                "number": self.Value.Number,
            }
        return {"id": self.ID, "name": self.Name, "option": self.Option.ID}

    def set_value(self, value):
        if not hasattr(self, "Value"):
            v = OptionValue()
            v.Key = self
            v.Value = str(value)
            v.Number = isinstance(value, int)
            v.save()
        else:
            self.Value.Value = str(value)
            self.Value.Number = isinstance(value, int)
            self.Value.save()

    def save(self, *args, **kwargs):
        self.Option.save()
        return super().save(*args, **kwargs)

    def rest_put(self, parent, data):
        if "name" not in data:
            return HttpError428("option key name")
        if parent is not None:
            self.Option = parent
        else:
            return HttpError428("option key options")
        self.Name = data["name"]
        self.save()
        if "value" in data:
            self.set_value(data["value"])
        return self.rest_json()

    def rest_delete(self, parent, name):
        if name is None:
            self.Option.save()
            self.delete()
        elif name == "value" and hasattr(self, "Value"):
            self.Value.delete()
            self.save()
        return None

    def rest_post(self, parent, name, data):
        if parent is not None:
            self.Option = parent
        if name is None:
            if "name" in data:
                self.Name = data["name"]
            if "value" in data:
                self.set_value(data["value"])
            self.save()
        else:
            if name == "name":
                self.Name = data
            elif name == "value":
                self.set_value(data)
            self.save()
        return self.rest_json()


class OptionValue(Model):
    class Meta:
        db_table = "option_values"
        verbose_name = "Option Value"
        verbose_name_plural = "Option Values"

    __parents__ = [("key", "OptionKey")]

    ID = AutoField(
        db_column="id",
        verbose_name="Option Value ID",
        null=False,
        primary_key=True,
        editable=False,
    )
    Key = OneToOneField(
        db_column="key",
        verbose_name="Option Value Key",
        null=False,
        on_delete=CASCADE,
        to="scorebot_db.OptionKey",
        related_name="Value",
    )
    Value = CharField(
        db_column="value",
        verbose_name="Option Value Data",
        null=True,
        max_length=255,
        blank=True,
    )
    Number = BooleanField(
        db_column="number",
        verbose_name="Option Value is Number",
        null=False,
        default=False,
    )

    def value(self):
        if self.Number:
            return self.Value
        return "'%s'" % self.Value

    def __str__(self):
        return "Value %s (%s)" % (self.Value, self.Key.fullname())

    def rest_json(self):
        return {
            "id": self.ID,
            "name": self.Key.Name,
            "name_id": self.Key.ID,
            "value": self.Value,
            "number": self.Number,
        }

    def save(self, *args, **kwargs):
        self.Key.Option.save()
        return super().save(*args, **kwargs)

    def rest_put(self, parent, data):
        if parent is None:
            return HttpError428("option value key")
        if "value" in data:
            self.Value = data["value"]
            self.Number = isinstance(data["value"], int) or "number" in data
        self.Key = parent
        self.save()
        return self.rest_json()

    def rest_delete(self, parent, name):
        if name is None:
            self.Key.Option.save()
            self.delete()
        elif name == "value":
            self.Value = None
            self.save()
        return None

    def rest_post(self, parent, name, data):
        if parent is not None:
            self.Key = parent
        if name is None and "value" in data:
            self.Value = data["value"]
            self.Number = isinstance(data["value"], int) or "number" in data
        elif name == "value":
            self.Value = data
            self.Number = isinstance(data, int)
        self.save()
        return self.rest_json()
