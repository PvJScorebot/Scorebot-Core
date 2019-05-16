#!/usr/bin/python3
# Scorebot UDP (Universal Development Platform)
#
# The Scorebot Project / iDigitalFlame 2019

from math import floor
from django.core.exceptions import ValidationError
from django.db.models import (
    Model,
    CharField,
    AutoField,
    ForeignKey,
    DateTimeField,
    IntegerField,
    OneToOneField,
    BigIntegerField,
    PositiveSmallIntegerField,
    CASCADE,
    SET_NULL,
)

CREDIT_TYPES = (
    (0, "Correction"),
    (1, "Transfer"),
    (2, "Purchase"),
    (3, "Payment"),
    (4, "Health"),
    (5, "Beacon"),
    (6, "Flag"),
    (7, "Ticket"),
    (8, "Achivement"),
    (9, "Event"),
)
TRANSFTER_STATUS = ((0, "Pending"), (1, "Approved"), (2, "Rejected"))


class Score(Model):
    class Meta:
        db_table = "score"
        verbose_name = "Score"
        verbose_name_plural = "Scores"

    ID = AutoField(
        db_column="id",
        verbose_name="Score ID",
        null=False,
        primary_key=True,
        editable=False,
    )
    Value = BigIntegerField(
        db_column="value", verbose_name="Score Value", null=False, default=0, editable=0
    )

    def Score(self):
        v = 0
        for c in self.Stack.all():
            v += c.Value
        if v != self.Value:
            self.Value = v
            self.save()
        del v
        return self.Value

    def __len__(self):
        return self.Value

    def __str__(self):
        return "Score-%d %dpts" % (self.ID, self.Score())


class Credit(Model):
    class Meta:
        ordering = ["Date"]
        db_table = "credits"
        get_latest_by = "Date"
        verbose_name = "Credit"
        verbose_name_plural = "Credit"

    ID = AutoField(
        db_column="id",
        verbose_name="Credit ID",
        null=False,
        primary_key=True,
        editable=False,
    )
    Date = DateTimeField(
        db_column="date",
        verbose_name="Credit Date",
        null=False,
        auto_now_add=True,
        blank=True,
    )
    Type = PositiveSmallIntegerField(
        db_column="type",
        verbose_name="Credit Type",
        null=False,
        default=0,
        choices=CREDIT_TYPES,
    )
    Value = IntegerField(
        db_column="value",
        verbose_name="Credit Value",
        null=False,
        default=0,
        blank=True,
    )
    Score = ForeignKey(
        db_column="score",
        verbose_name="Credit Parent",
        null=False,
        on_delete=CASCADE,
        to="scorebot_db.Score",
        related_name="Stack",
    )
    Sender = ForeignKey(
        db_column="sender",
        verbose_name="Credit Sender",
        null=True,
        on_delete=SET_NULL,
        to="scorebot_db.Team",
        related_name="SentCredits",
    )
    Receiver = ForeignKey(
        db_column="receiver",
        verbose_name="Credit Receiver",
        null=True,
        on_delete=SET_NULL,
        to="scorebot_db.Team",
        related_name="ReceivedCredits",
    )

    def __str__(self):
        s = str(self.Subclass())
        if len(s) == 0:
            return "[%s]: %s -> %s (%dpts) on %s" % (
                CREDIT_TYPES[self.Type][1],
                self.Sender.Fullname(),
                self.Receiver.Fullname(),
                self.Value,
                self.Date.strftime("%m/%d/%y %H:%M"),
            )
        return "%s [%s]: %s -> %s (%dpts) on %s" % (
            s,
            CREDIT_TYPES[self.Type][1],
            self.Sender.Fullname(),
            self.Receiver.Fullname(),
            self.Value,
            self.Date.strftime("%m/%d/%y %H:%M"),
        )

    def Subclass(self):
        n = "Subclass_%s" % CREDIT_TYPES[self.Type][1].lower()
        if hasattr(self, n):
            return getattr(self, n)
        return None

    def save(self, *args, **kwargs):
        if self.Sender.GetGame().ID != self.Receiver.GetGame().ID:
            raise ValidationError(
                'Receiving team "%(receiver)s" is not in the same game as the Sending team "%(sender)s"',
                code="invalid",
                params={"receiver": self.Receiver.Name, "sender": self.Sender.Name},
            )
        super().save(*args, **kwargs)


class Transaction(Model):
    class Meta:
        abstract = True

    ID = AutoField(
        db_column="id",
        verbose_name="Transaction ID",
        null=False,
        primary_key=True,
        editable=False,
    )

    Credit = OneToOneField(
        db_column="credit",
        verbose_name="Transaction Credit",
        null=False,
        on_delete=CASCADE,
        to="scorebot_db.Credit",
        related_name="Subclass_%(class)s",
    )

    def __str__(self):
        return ""

    def save(self, *args, **kwargs):
        if CREDIT_TYPES[self.Credit.Type][1] != self.__class__.__name__:
            raise ValidationError(
                'Credit type "%(this)s" cannot be assigned to a credit of type "%(type)s"',
                code="invalid",
                params={
                    "this": self.__class__.__name__,
                    "type": CREDIT_TYPES[self.Credit.Type][1],
                },
            )
        super().save(*args, **kwargs)


class Flag(Transaction):
    class Meta:
        db_table = "credits_flag"
        verbose_name = "Flag Credit"
        verbose_name_plural = "Flag Credits"

    Flag = None


class Event(Transaction):
    class Meta:
        db_table = "credits_event"
        verbose_name = "Event Credit"
        verbose_name_plural = "Event Credits"

    Details = CharField(
        db_column="details",
        verbose_name="Event Details",
        null=True,
        blank=True,
        max_length=255,
    )

    def __str__(self):
        return self.Details


class Ticket(Transaction):
    class Meta:
        db_table = "credits_ticket"
        verbose_name = "Ticket Credit"
        verbose_name_plural = "Ticket Credits"

    Ticket = None


class Health(Transaction):
    class Meta:
        db_table = "credits_health"
        verbose_name = "Health Credit"
        verbose_name_plural = "Health Credit"

    Expected = IntegerField(
        db_column="expected", verbose_name="Expected Credits", null=False, default=0
    )

    def __str__(self):
        p = self.Credit.Value
        return "Payment %d%% (%d/%d)" % (
            floor((float(p) / float(self.Expected)) * float(100)),
            p,
            self.Expected,
        )


class Beacon(Transaction):
    class Meta:
        db_table = "credits_beacon"
        verbose_name = "Beacon Credit"
        verbose_name_plural = "Beacon Credits"

    Beacon = None


class Payment(Transaction):
    class Meta:
        db_table = "credits_payment"
        verbose_name = "Payment Credit"
        verbose_name_plural = "Payment Credits"

    Team = ForeignKey(
        db_column="team",
        verbose_name="Target Team",
        null=False,
        on_delete=CASCADE,
        to="scorebot_db.Team",
    )

    def __str__(self):
        return self.Team.Name


class Transfer(Transaction):
    class Meta:
        db_table = "credits_transfer"
        verbose_name = "Transfer Credit"
        verbose_name_plural = "Transfer Credits"

    Expected = IntegerField(
        db_column="expected", verbose_name="Transfer Credits", null=False, default=0
    )
    Status = PositiveSmallIntegerField(
        db_column="status",
        verbose_name="Transfer Status",
        null=False,
        default=0,
        choices=TRANSFTER_STATUS,
    )

    def __str__(self):
        return self.get_Status_display()


class Purchase(Transaction):
    class Meta:
        db_table = "credits_purchase"
        verbose_name = "Purchase Credit"
        verbose_name_plural = "Purchase Credits"

    Item = ForeignKey(
        db_column="item",
        verbose_name="Purchased Item",
        null=True,
        on_delete=SET_NULL,
        to="scorebot_db.Purchase",
        related_name="Purchases",
        blank=True,
    )
    Description = CharField(
        db_column="description",
        verbose_name="Purchase Description",
        null=True,
        max_length=255,
    )

    def __str__(self):
        if self.Item is not None:
            return "%s" % self.Item
        return self.Description


class Achivement(Transaction):
    class Meta:
        db_table = "credits_goal"
        verbose_name = "Achivement Credit"
        verbose_name_plural = "Achivement Credits"

    Details = CharField(
        db_column="details",
        verbose_name="Achivement Details",
        null=True,
        blank=True,
        max_length=255,
    )

    def __str__(self):
        return self.Details


class Correction(Transaction):
    class Meta:
        db_table = "credits_correction"
        verbose_name = "Correction Credit"
        verbose_name_plural = "Correction Credits"

    Notes = CharField(
        db_column="notes",
        verbose_name="Correction Notes",
        null=True,
        blank=True,
        max_length=1024,
    )
