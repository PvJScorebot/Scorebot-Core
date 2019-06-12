#!/usr/bin/python3
# Scorebot UDP (Universal Development Platform)
#
# The Scorebot Project / iDigitalFlame 2019

from math import floor
from django.db.transaction import atomic
from django.core.exceptions import ValidationError
from scorebot_utils.restful import HttpError428, HttpError404
from scorebot_utils.constants import CREDIT_TYPES, TRANSFTER_STATUS
from scorebot_utils.generic import is_model, create_model, get_by_id
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


def new_transaction(credit, sender, receiver, data, auto=True):
    try:
        credit.Value = int(data["value"])
    except ValueError:
        raise HttpError428("credit value is a number")
    credit.Type = -1
    if "type" in data:
        try:
            credit.Type = int(data["type"])
        except ValueError:
            raise HttpError428("credit type is a number")
        else:
            if not (0 < credit.Type < len(CREDIT_TYPES)):
                raise HttpError428("credit type is out of bounds")
    elif "type" in data["transaction"]:
        type_name = data["transaction"]["type"].lower()
        for t in CREDIT_TYPES:
            if t[1].lower() == type_name:
                credit.Type = t[0]
                break
        del type_name
    if credit.Type == -1:
        raise HttpError428("credit type is invalid")
    send_trans = None
    recv_trans = create_model(CREDIT_TYPES[credit.Type][1])
    with atomic():
        credit.save()
        recv_trans.from_json(data["transaction"])
        if receiver is None and sender is not None:
            credit.Value = recv_trans.get_pair_value(credit.Value)
        recv_trans.Credit = credit
        recv_trans.save()
        if sender is not None and auto and receiver is not None:
            send_credit = Credit()
            send_credit.Score = sender
            send_credit.Type = credit.Type
            send_credit.Sender = credit.Sender
            send_credit.Reciver = credit.Reciver
            send_credit.Value = recv_trans.get_pair_value(credit.Value)
            send_credit.Paired = credit
            send_credit.save()
            send_trans = create_model(CREDIT_TYPES[credit.Type][1])
            send_trans.from_json(data["transaction"])
            send_trans.Credit = send_credit
            send_trans.save()
            sender.update()
            del send_credit
        credit.update()
    return (recv_trans, send_trans)


class Score(Model):
    class Meta:
        db_table = "scores"
        verbose_name = "Score"
        verbose_name_plural = "Scores"

    __parents__ = [("team", "PlayerTeam"), ("team", "ScoringTeam")]

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

    def score(self):
        v = 0
        for c in self.Stack.all():
            v += c.Value
        if v != self.Value:
            self.Value = v
            self.save()
        del v
        return self.Value

    def update(self):
        self.Score()

    def __len__(self):
        return max(self.Value, 0)

    def __str__(self):
        if hasattr(self, "Owner"):
            return "Score[%d; %s] %dpts" % (self.ID, self.Owner.fullname(), self.Value)
        return "Score[%d] %dpts" % (self.ID, self.Value)

    def rest_json(self):
        return {"id": self.ID, "value": self.Value}

    def rest_put(self, parent, data):
        if parent is not None:
            if is_model(parent, "PlayerTeam"):
                parent.Team.Score = self
                parent.Team.save()
            else:
                parent.Score = self
                parent.save()
        return self.rest_json()

    def rest_delete(self, parent, name):
        if name is None:
            self.delete()
        return None

    def rest_post(self, parent, name, data):
        return self.rest_post(parent, data)


class Credit(Model):
    class Meta:
        ordering = ["Date"]
        db_table = "credits"
        get_latest_by = "Date"
        verbose_name = "Credit"
        verbose_name_plural = "Credit"

    __parents__ = [("score", "Score")]

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
        editable=False,
    )
    Type = PositiveSmallIntegerField(
        db_column="type",
        verbose_name="Credit Type",
        null=False,
        default=0,
        choices=CREDIT_TYPES,
        editable=False,
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
    Paired = OneToOneField(
        db_column="pair",
        verbose_name="Credit Pair",
        null=True,
        on_delete=CASCADE,
        to="scorebot_db.Credit",
        related_name="Cause",
        editable=False,
    )

    def __str__(self):
        s = str(self.subclass())
        if len(s) == 0:
            return "[%s]: %s -> %s (%dpts) on %s" % (
                CREDIT_TYPES[self.Type][1],
                self.Sender.fullname(),
                self.Receiver.fullname(),
                self.Value,
                self.Date.strftime("%m/%d/%y %H:%M"),
            )
        return "%s [%s]: %s -> %s (%dpts) on %s" % (
            s,
            CREDIT_TYPES[self.Type][1],
            self.Sender.fullname(),
            self.Receiver.fullname(),
            self.Value,
            self.Date.strftime("%m/%d/%y %H:%M"),
        )

    def subclass(self):
        n = "Subclass_%s" % CREDIT_TYPES[self.Type][1].lower()
        print("type id >>", self.Type, n)
        if hasattr(self, n):
            return getattr(self, n)
        return None

    def rest_json(self):
        r = {
            "id": self.ID,
            "date": self.Date.isoformat(),
            "type": self.Type,
            "score": self.Score.ID,
            "receiver": self.Receiver.ID,
            "sender": self.Sender.ID,
            "value": self.Value,
            "transaction": self.subclass().rest_json(),
        }
        r["transaction"]["type"] = CREDIT_TYPES[self.Type][1].lower()
        if self.Paired is not None:
            r["paried"] = self.Paired.ID
        return r

    def set_value(self, value):
        self.Value = value
        if self.Paired is not None:
            with atomic():
                self.Paired.Value = value
                self.Paired.save()
                self.Paired.Score.update()
                self.save()
                self.Score.update()
        else:
            self.save()
            self.Score.update()

    def save(self, *args, **kwargs):
        if self.Sender.game().ID != self.Receiver.game().ID:
            raise ValidationError(
                'Receiving team "%(receiver)s" is not in the same game as the Sending team "%(sender)s"',
                code="invalid",
                params={"receiver": self.Receiver.Name, "sender": self.Sender.Name},
            )
        super().save(*args, **kwargs)

    def rest_put(self, parent, data):
        if "sender" not in data:
            return HttpError428("credit sender")
        if "value" not in data:
            return HttpError428("credit value")
        if "transaction" not in data or not isinstance(data["transaction"], dict):
            return HttpError428("credit transaction must be a dict")
        receiver_team = None
        sender_team = get_by_id("Team", data["sender"])
        if sender_team is None:
            return HttpError404("sender id")
        if parent is None and "receiver" in data:
            receiver_team = get_by_id("Team", data["receiver"])
            if receiver_team is None:
                return HttpError404("receiver id")
        elif parent is not None and hasattr(parent, "Owner"):
            receiver_team = parent.Owner
        else:
            return HttpError428("credit receiver has no assigned Team")
        self.Sender = sender_team.base()
        self.Receiver = sender_team.base()
        rs = receiver_team.score()
        if rs is None:
            self.Score = self.Sender.score()
        else:
            self.Score = rs
        del receiver_team
        new_transaction(self, sender_team.score(), rs, data, True)
        del rs
        del sender_team
        return self.rest_json()

    def rest_delete(self, parent, name):
        if name is None:
            with atomic():
                if self.Paired is not None:
                    s = self.Paired.Score
                    self.Paired.delete()
                    s.Update()
                s = self.Score
                self.delete()
                s.Update()
            return None
        if name == "value":
            with atomic():
                if self.Paired is not None:
                    self.Paired.Value = 0
                    self.Paired.save()
                    self.Paired.Score.Update()
                self.Value = 0
                self.save()
                self.Score.Update()
        return None

    def rest_post(self, parent, name, data):
        if name is None:
            if "value" in data:
                try:
                    self.set_value(data["value"])
                except ValueError:
                    return HttpError428("value is a number")
            s = self.subclass()
            if self.Paired is not None:
                sp = self.Paired.subclass()
                sp.from_json(data)
                s.from_json(data)
                with atomic():
                    s.save()
                    sp.save()
            else:
                s.from_json(data)
                s.save()
        elif name == "value":
            try:
                self.set_value(int(data))
            except ValueError:
                return HttpError428("value is a number")
        return self.rest_json()


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
        return "%d" % self.ID

    def rest_json(self):
        return {"id": self.ID}

    def from_json(self, data):
        pass

    def get_pair_value(self, value):
        return value * -1

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


class Steal(Transaction):
    class Meta:
        db_table = "credits_flag"
        verbose_name = "Flag Credit"
        verbose_name_plural = "Flag Credits"

    __hidden__ = True

    Flag = None


class Event(Transaction):
    class Meta:
        db_table = "credits_event"
        verbose_name = "Event Credit"
        verbose_name_plural = "Event Credits"

    __hidden__ = True

    Details = CharField(
        db_column="details",
        verbose_name="Event Details",
        null=True,
        blank=True,
        max_length=255,
    )

    def __str__(self):
        return self.Details

    def rest_json(self):
        return {"id": self.ID, "details": self.Details}


class Ticket(Transaction):
    class Meta:
        db_table = "credits_ticket"
        verbose_name = "Ticket Credit"
        verbose_name_plural = "Ticket Credits"

    __hidden__ = True

    Ticket = None


class Health(Transaction):
    class Meta:
        db_table = "credits_health"
        verbose_name = "Health Credit"
        verbose_name_plural = "Health Credit"

    __hidden__ = True

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

    def rest_json(self):
        return {"id": self.ID, "expected": self.Expected}


class Beacon(Transaction):
    class Meta:
        db_table = "credits_beacon"
        verbose_name = "Beacon Credit"
        verbose_name_plural = "Beacon Credits"

    __hidden__ = True

    Beacon = None


class Payment(Transaction):
    class Meta:
        db_table = "credits_payment"
        verbose_name = "Payment Credit"
        verbose_name_plural = "Payment Credits"

    __hidden__ = True

    Team = ForeignKey(
        db_column="team",
        verbose_name="Target Team",
        null=False,
        on_delete=CASCADE,
        to="scorebot_db.Team",
    )

    def __str__(self):
        return self.Team.Name

    def rest_json(self):
        return {"id": self.ID, "target": self.Team.ID}


class Transfer(Transaction):
    class Meta:
        db_table = "credits_transfer"
        verbose_name = "Transfer Credit"
        verbose_name_plural = "Transfer Credits"

    __hidden__ = True

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

    def rest_json(self):
        return {"id": self.ID, "expected": self.Expected, "status": self.Status}


class Purchase(Transaction):
    class Meta:
        db_table = "credits_purchase"
        verbose_name = "Purchase Credit"
        verbose_name_plural = "Purchase Credits"

    __hidden__ = True

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

    def rest_json(self):
        if self.Item is not None:
            return {
                "id": self.ID,
                "description": self.Description,
                "item": self.Item.ID,
            }
        return {"id": self.ID, "description": self.Description}


class Achivement(Transaction):
    class Meta:
        db_table = "credits_goal"
        verbose_name = "Achivement Credit"
        verbose_name_plural = "Achivement Credits"

    __hidden__ = True

    Details = CharField(
        db_column="details",
        verbose_name="Achivement Details",
        null=True,
        blank=True,
        max_length=255,
    )

    def __str__(self):
        return self.Details

    def rest_json(self):
        return {"id": self.ID, "details": self.Details}


class Correction(Transaction):
    class Meta:
        db_table = "credits_correction"
        verbose_name = "Correction Credit"
        verbose_name_plural = "Correction Credits"

    __hidden__ = True

    Notes = CharField(
        db_column="notes",
        verbose_name="Correction Notes",
        null=True,
        blank=True,
        max_length=1024,
    )

    def rest_json(self):
        if self.Notes is not None:
            return {"id": self.ID, "notes": self.Notes}
        return {"id": self.ID}

    def from_json(self, data):
        if "notes" in data:
            self.Notes = data["notes"]
