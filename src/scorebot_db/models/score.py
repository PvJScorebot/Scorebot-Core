#!/usr/bin/false
# Scorebot Scoring Django Models
# Scorebot v4 - The Scorebot Project
#
# Copyright (C) 2020 iDigitalFlame
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#


from math import floor
from scorebot.util import new
from scorebot import Scoring, Events
from django.utils.timezone import now
from scorebot.constants import ScoreConstants, CORRECTIONS
from django.db.models import Model, BooleanField, ForeignKey, OneToOneField, DateTimeField, IntegerField, CASCADE, \
                             PositiveSmallIntegerField, SET_NULL


class Transaction(Model):
    """
    Transaction:
        Scorebot Score Base

        Defines a Base Python Class object for tracking and managing score types, results and values. Allows for
        tracking of the "score stack", which is a history of all Transactions for a Team over time.

                Subclasses Must Define:
            save        ()
            __json__    ()
            __score__   ()
            __string__  ()
    """
    class Meta:
        verbose_name = '[Score] Transaction'
        verbose_name_plural = '[Score] Transaction'

    value = IntegerField('Transaction Value', default=0)
    when = DateTimeField('Transaction Date/Time', auto_now_add=True)
    previous = OneToOneField('self', null=True, blank=True, on_delete=SET_NULL)
    source = ForeignKey('scorebot_db.Team', on_delete=CASCADE, related_name='payer')
    destination = ForeignKey('scorebot_db.Team', on_delete=CASCADE, related_name='receiver')
    subclass = PositiveSmallIntegerField('Team SubClass', default=None, null=True, editable=False,
                                         choices=ScoreConstants.SUBCLASS)

    def log(self):
        # Log the Score to a Flat File (Triggered on Saves).
        #
        # Columns
        # Value, Type, ISO When, Path From, Path To, Score
        Scoring.info('%d,%s,%s,%s,%s,%d' % (
            self.score(), self.name(), self.when.isoformat(), self.source.path(),
            self.destination.path(), self.destination.score()
        ))

    def name(self):
        return str(self.__subclass__().__class__.__name__)

    def json(self):
        return self.__subclass__().__json__()

    def score(self):
        return self.__subclass__().__score__()

    def stack(self):
        total = 0
        score = self
        stack = list()
        while score is not None:
            stack.append(score.json())
            total += score.score()
            score = next(score)
        result = {
            'stack': stack, 'total': total
        }
        del stack
        del total
        return result

    def total(self):
        if self.previous is not None:
            return self.score() + self.previous.score()
        return self.score()

    def reverse(self):
        transaction = new(self.name(), save=False)
        transaction.when = self.when
        transaction.subclass = self.subclass
        transaction.value = self.score() * -1
        transaction.destination = self.source
        transaction.source = self.destination
        transaction.save()
        return transaction

    def __str__(self):
        return self.__subclass__().__string__()

    def __len__(self):
        return abs(self.score())

    def __next__(self):
        return self.previous

    def __bool__(self):
        return self.score() > 0

    def __json__(self):
        return {
            'type': self.name(), 'value': self.get_score(),
            'when': self.when.isoformat(), 'source': self.source.name,
            'destination': self.destination.name
        }

    def __score__(self):
        return self.value

    def __string__(self):
        return '[Transaction] (%s) %d: %s -> %s' % (
            self.when.strftime('%m/%d/%y %H:%M'), self.value, self.source.path(), self.destination.path()
        )

    def __subclass__(self):
        if self.subclass == ScoreConstants.TRANSACTION or self.__class__.__name__ == self.get_subclass_display():
            return self
        if self.subclass == ScoreConstants.PAYMENT:
            return self.payment
        if self.subclass == ScoreConstants.TRANSFER:
            return self.transfer
        if self.subclass == ScoreConstants.PURCHASE:
            return self.purchase
        if self.subclass == ScoreConstants.CORRECTION:
            return self.correction
        if self.subclass == ScoreConstants.PAYMENTHEALTH:
            return self.paymenthealth
        if self.subclass == ScoreConstants.TRANSFERRESULT:
            return self.transferresult
        if self.subclass == ScoreConstants.TRANSACTIONFLAG:
            return self.transactionflag
        if self.subclass == ScoreConstants.TRANSACTIONBEACON:
            return self.transactionbeacon
        return self

    def __lt__(self, other):
        return isinstance(other, Transaction) and other.score() > self.score()

    def __gt__(self, other):
        return isinstance(other, Transaction) and other.score() < self.score()

    def __eq__(self, other):
        return isinstance(other, Transaction) and other.score() == self.score()

    def save(self, *args, **kwargs):
        if self.subclass is None:
            self.subclass = ScoreConstants.TRANSACTION
        Model.save(self, *args, **kwargs)


class Payment(Transaction):
    class Meta:
        verbose_name = '[Score] Payment'
        verbose_name_plural = '[Score] Payments'

    target = ForeignKey('scorebot_db.PlayerTeam', on_delete=CASCADE, related_name='payments')

    def process(self):
        payment = max(floor(float(self.score() * float((100 - self.target.deduction) / 100))), 0)
        result = new('PaymentHealth', save=False)
        result.value = payment
        result.expected = self.score()
        result.source = self.destination
        result.destination = self.target
        result.save()
        self.target.append(result)
        Events.info('Payment from "%s" of "%d" via "%s" was issued to "%s" as "%d" (%d%% deduction).' % (
            self.source.path(), self.score(), self.destination.path(), self.target.path(), payment,
            self.target.deduction
        ))
        self.log()
        del payment
        return result

    def __json__(self):
        return {
            'type': self.name(), 'value': self.value,
            'when': self.when.isoformat(), 'target': self.target.name,
            'source': self.source.name, 'destination': self.destination.name
        }

    def __string__(self):
        return '[Payment] (%s) %d PTS: %s -> %s (%s)' % (
            self.when.strftime('%m/%d/%y %H:%M'), self.value, self.source.path(), self.destination.path(),
            self.target.path()
        )

    def save(self, *args, **kwargs):
        if self.subclass is None:
            self.subclass = ScoreConstants.PAYMENT
        Transaction.save(self, *args, **kwargs)


class Transfer(Transaction):
    class Meta:
        verbose_name = '[Score] Transfer'
        verbose_name_plural = '[Score] Transfer'

    processed = BooleanField('Tranfer Processed', default=False)
    approved = DateTimeField('Tansfer Approved', default=None, null=True, blank=True)

    def approve(self):
        return self.transfer(True)

    def disapprove(self):
        return self.transfer(False)

    def __string__(self):
        return '[Transfer] (%s) %d [%s] PTS: %s -> %s' % (
            self.when.strftime('%m/%d/%y %H:%M'), self.value, 'Approved' if self.approved else 'Pending',
            self.source.path(), self.destination.path()
        )

    def save(self, *args, **kwargs):
        if self.subclass is None:
            self.subclass = ScoreConstants.TRANSFER
        Transaction.save(self, *args, **kwargs)

    def transfer(self, approve=True):
        self.approved = now()
        self.processed = True
        if not approve:
            Events.info('Score Transfer from "%s" to "%s" of "%d" PTS was disapproved, returning "%d" PTS to "%s"!' % (
                self.source.path(), self.destination.path(), self.value, self.value, self.source.path()
            ))
            result = new('TransferResult', save=False)
            result.value = self.value
            result.source = self.source
            result.destination = self.source
            result.save()
            return self.source.append(result)
        result = new('TransferResult', save=False)
        result.source = self.source
        result.value = self.value * -1
        result.destination = self.destination
        result.save()
        Events.info('Score Transfer from "%s" to "%s" of "%d" PTS was approved, transfer "%d" PTS to "%s"!' % (
            self.source.path(), self.destination.path(), self.value, self.value, self.destination.path()
        ))
        self.save()
        self.source.append(result)
        return self.destination.append(self)


class Purchase(Transaction):
    class Meta:
        verbose_name = '[Score] Purchase'
        verbose_name_plural = '[Score] Purchases'

    item = ForeignKey('scorebot_db.Item', blank=True, null=True, on_delete=SET_NULL, related_name='purchases')

    def __json__(self):
        return {
            'type': self.name(), 'value': self.score(),
            'item': self.json(), 'when': self.when.isoformat(),
            'source': self.source.name, 'destination': self.destination.name
        }

    def __score__(self):
        return self.value * -1

    def __string__(self):
        return '[Purchase] (%s) %s: %d PTS: %s' % (
            self.when.strftime('%m/%d/%y %H:%M'), self.item.name, self.value, self.source.path()
        )

    def save(self, *args, **kwargs):
        if self.subclass is None:
            self.subclass = ScoreConstants.PURCHASE
        Transaction.save(self, *args, **kwargs)


class Correction(Transaction):
    class Meta:
        verbose_name = '[Score] Correction'
        verbose_name_plural = '[Score] Correction'

    reason = PositiveSmallIntegerField('Correction Reason', default=0, choices=CORRECTIONS)

    def __json__(self):
        return {
            'type': self.name(), 'value': self.value,
            'when': self.when.isoformat(), 'source': self.source.name,
            'reason': self.get_reason_display(), 'destination': self.destination.name
        }

    def __string__(self):
        return '[Correction] (%s) %s %d PTS: %s -> %s' % (
            self.when.strftime('%m/%d/%y %H:%M'), self.get_reason_display(), self.value, self.source.path(),
            self.destination.path()
        )

    def save(self, *args, **kwargs):
        if self.subclass is None:
            self.subclass = ScoreConstants.CORRECTION
        Transaction.save(self, *args, **kwargs)


class PaymentHealth(Transaction):
    class Meta:
        verbose_name = '[Score] Health Payment'
        verbose_name_plural = '[Score] Health Payments'

    expected = IntegerField('Expected Payment Value')

    def __json__(self):
        return {
            'type': self.name(), 'value': self.value,
            'expected': self.expected, 'when': self.when.isoformat(),
            'source': self.source.name, 'destination': self.destination.name
        }

    def __string__(self):
        if self.value == 0:
            return '[PaymentHealth] (%s) %d/%d PTS: %s -> %s (0%%)' % (
                self.when.strftime('%m/%d/%y %H:%M'), self.value, self.expected, self.source.path(),
                self.destination.path()
            )
        return '[PaymentHealth] (%s) %d/%d PTS: %s -> %s (%s%%)' % (
            self.when.strftime('%m/%d/%y %H:%M'), self.value, self.expected, self.source.path(),
            self.destination.path(), floor(float(self.expected / self.value) * 100)
        )

    def save(self, *args, **kwargs):
        if self.subclass is None:
            self.subclass = ScoreConstants.PAYMENTHEALTH
        Transaction.save(self, *args, **kwargs)


class TransferResult(Transaction):
    class Meta:
        verbose_name = '[Score] Transfer Result'
        verbose_name_plural = '[Score] Transfer Result'

    def __string__(self):
        return '[TransferResult] (%s) %d PTS: %s -> %s' % (
            self.when.strftime('%m/%d/%y %H:%M'), self.value, self.source.path(), self.destination.path()
        )

    def save(self, *args, **kwargs):
        if self.subclass is None:
            self.subclass = ScoreConstants.TRANSFERRESULT
        Transaction.save(self, *args, **kwargs)


class TransactionFlag(Transaction):
    class Meta:
        verbose_name = '[Score] Flag Transaction'
        verbose_name_plural = '[Score] Flag Transactions'

    flag = ForeignKey('scorebot_db.Flag', on_delete=CASCADE, related_name='transaction')

    def __json__(self):
        return {
            'type': self.name(), 'value': self.value,
            'flag': self.flag.name, 'when': self.when.isoformat(),
            'source': self.source.name, 'destination': self.destination.name
        }

    def __string__(self):
        return '[TransactionFlag] (%s) %s: %d PTS: %s -> %s' % (
            self.when.strftime('%m/%d/%y %H:%M'), self.flag.name, self.value, self.source.path(),
            self.destination.path()
        )

    def save(self, *args, **kwargs):
        if self.subclass is None:
            self.subclass = ScoreConstants.TRANSACTIONFLAG
        Transaction.save(self, *args, **kwargs)


class TransactionBeacon(Transaction):
    class Meta:
        verbose_name = '[Score] Beacon Transaction'
        verbose_name_plural = '[Score] Beacon Transactions'

    beacon = ForeignKey('scorebot_db.Beacon', on_delete=CASCADE, related_name='transactions')

    def __json__(self):
        return {
            'type': self.name(), 'value': self.value,
            'when': self.when.isoformat(), 'beacon': self.beacon.path(),
            'source': self.source.name, 'destination': self.destination.name
        }

    def __string__(self):
        return '[TransactionBeacon] (%s) %s: %d PTS: %s -> %s' % (
            self.when.strftime('%m/%d/%y %H:%M'), self.beacon.path(), self.value, self.source.path(),
            self.destination.path()
        )

    def save(self, *args, **kwargs):
        if self.subclass is None:
            self.subclass = ScoreConstants.TRANSACTIONBEACON
        Transaction.save(self, *args, **kwargs)
