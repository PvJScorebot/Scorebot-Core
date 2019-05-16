#!/usr/bin/python3
# Scorebot UDP (Universal Development Platform)
#
# The Scorebot Project / iDigitalFlame 2019

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

    def Contains(self, name):
        try:
            self.Keys.all().get(Name__iexact=name)
        except ObjectDoesNotExist:
            return False
        return True

    def Set(self, name, value):
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

    def Get(self, name, default=None):
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


class OptionKey(Model):
    class Meta:
        db_table = "option_keys"
        verbose_name = "Option Key"
        verbose_name_plural = "Option Keys"

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
            return "Key '%s' = %s" % (self.Fullname(), self.Value.PrintValue())
        return "Key '%s'" % self.Fullname()

    def Fullname(self):
        if self.Option is None:
            return self.Name
        return "%s\%s" % (self.Option.Name, self.Name)


class OptionValue(Model):
    class Meta:
        db_table = "option_values"
        verbose_name = "Option Value"
        verbose_name_plural = "Option Values"

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

    def __str__(self):
        return "Value %s (%s)" % (self.Value, self.Key.Fullname())

    def PrintValue(self):
        if self.Number:
            return self.Value
        return "'%s'" % self.Value
