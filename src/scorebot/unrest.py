#!/usr/bin/false
#
# UnReSTFul API

from json import dumps, JSONDecodeError
from django.core.serializers import serialize
from django.conf.urls import url
from django.db.models import AutoField, IntegerField, CharField, ManyToManyField, ManyToOneRel, OneToOneField, \
                             ForeignKey, ManyToManyRel, QuerySet
from django.db.models.base import ModelBase
from django.core.exceptions import ValidationError, ObjectDoesNotExist, MultipleObjectsReturned
from django.http import HttpResponseBadRequest, HttpResponseForbidden, HttpResponse, JsonResponse

RegisteredModels = dict()


class UnRestResponse(HttpResponse):
    def __init__(self, content, status=200, data=None, raw=False):
        if raw:
            HttpResponse.__init__(self, status=status, content=str(content), content_type='text/plain')
        else:
            if isinstance(content, QuerySet):
                response = serialize('json', content, indent=4)
            elif isinstance(content, dict):
                response = dumps(content, indent=4)
            else:
                response = dumps({'result': str(content)}, indent=4)
            HttpResponse.__init__(self, status=status, content=response, content_type='application/json')
            del response

"""
Objects Check the stack above them to see if they are able to be grabbed,

ex

/team/3/ranges/

Will
 - Get Team.objects.get(id=3)
  - Then return team.ranges.all()

/team/3/ranges/1/

Will
 - Get Team.objects.get(id=3)
  - Then return team.ranges.get(id=1)

"""
class UnRested(object):
    def __init__(self, model):
        self.parent = None
        self.model = model
        self.params = list()
        self.name = model._meta.model_name.lower()

    def url(self, base):
        return '%s/%s/$' % self.name

    def resolve(self, kwargs, parms=None):
        pass

    def unrest(self, request, *args, **kwargs):
        if request.method == 'GET':
            pass



class UnRestObject(UnRested):
    def __init__(self, model):
        UnRestObject.__init__(self, model)

    def setup(self, base, urlpatterns):
        self.params.append(self.name)
        urlpatterns.append('%s/%s/$')


class UnRestField(UnRestObject):
    pass


class UnRestLookup(UnRestObject):
    pass


def unrest(request, *args, **kwargs):
    print(str(kwargs))
    if 'model' not in kwargs:
        return UnRestResponse(status=500, content='Missing Model Parameters!')
    if request.method == 'GET':
        model = RegisteredModels.get(kwargs['model'], None)
        if model is None:
            return UnRestResponse(status=404, content='Un-Registered Model class "%s"!' % kwargs['model'])
        if 'field' in kwargs and '%s_id' % kwargs['field'] in kwargs:
            query = kwargs.get('%s_id' % kwargs['field'], None)
            del kwargs['field']
        else:
            query = kwargs.get('%s_id' % kwargs['model'], None)
        print(model, query, str(kwargs))
        if query is not None:
            try:
                result = model.objects.filter(id=int(query), **request.GET.dict())
            except ValueError as err:
                return UnRestResponse(status=400, content=str(err))
            except ObjectDoesNotExist:
                return UnRestResponse(status=404, content='%s: %s' % (kwargs['model'].title(), query))
            except MultipleObjectsReturned:
                return UnRestResponse(staus=400, content='Multiple \'%s\' for \'%s\'!' % (
                    kwargs['model'].title(), query
                ))
            except Exception as err:
                return UnRestResponse(status=500, content=str(err))
            if len(result) == 0:
                return UnRestResponse(status=404, content='%s: %s' % (kwargs['model'].title(), query))
            if 'field' in kwargs and len(result) == 1:
                try:
                    return UnRestResponse(content=getattr(result[0], kwargs['field']), raw=True)
                except AttributeError as err:
                    pass
                return UnRestResponse(status=404, content='Unknown Field "%s" for "%s"!' % (
                    kwargs['field'], kwargs['model']
                ))
        else:
            try:
                result = model.objects.filter(**request.GET.dict())
            except Exception as err:
                return UnRestResponse(status=500, content=str(err))
        return UnRestResponse(content=result)
    return HttpResponse(str(args))


def init(models, urlpatterns, prefix='', debug=False):
    if isinstance(prefix, str) and len(prefix) > 0:
        if prefix[0] == '/':
            prefix = prefix[1:]
        if prefix[len(prefix) - 1] == '/':
            prefix = prefix[:len(prefix) - 1]
        base = prefix
    else:
        base = ''
    print('UnReSTFul API started, loading models on URL base path "/%s"..' % base)
    for model in models:
        if isinstance(model, ModelBase):
            name = model._meta.model_name.lower()
            if debug:
                print('UnReSTFul API: Registering Model "%s"..' % name)
            RegisteredModels[name.lower()] = model
            _register(dict(), model, None, base, urlpatterns, debug)
    del base


def _register(recurse, model, field, base, urlpatterns, debug):
    name = model._meta.model_name.lower()
    if name in recurse:
        return
    else:
        recurse[name] = True
    if field is not None:
        if field.name in recurse:
            return
        else:
            recurse[field.name] = True
    if field is None:
        path = '%s/%s' % (base, name)
    else:
        path = '%s/%s' % (base, field.name)
    if field is None:
        urlpatterns.append(url('^%s/$' % path, unrest, kwargs={'model': name}))
        if debug:
            print('UnReSTFul API: Registered Model "%s" URL: "^%s/$"..' % (name, path))
        path = '%s/(?P<%s_id>[0-9]+)' % (path, name)
        urlpatterns.append(url('^%s/$' % path, unrest, kwargs={'model': name}))
        if debug:
            print('UnReSTFul API: Registered Model "%s" URL: "^%s/$"..' % (name, path))
    elif isinstance(field, ManyToManyField) or isinstance(field, ManyToOneRel):
        urlpatterns.append(url('^%s/$' % path, unrest, kwargs={'model': name, 'field': field.name}))
        if debug:
            print('UnReSTFul API: Registered Model "%s" URL: "^%s/$"..' % (name, path))
        path = '%s/(?P<%s_id>[0-9]+)' % (path, field.name)
        urlpatterns.append(url('^%s/$' % path, unrest, kwargs={'model': name, 'field': field.name}))
        if debug:
            print('UnReSTFul API: Registered Model "%s" URL: "^%s/$"..' % (name, path))
    fields = None
    try:
        fields = getattr(model, '_meta').get_fields()
    except AttributeError:
        pass
    else:
        for field in fields:
            if '_ptr' in field.name:
                pass
            if isinstance(field, ForeignKey) or isinstance(field, ManyToManyField) or isinstance(field, OneToOneField):
                print('M2T: %s' % field.name, path) # _register(recurse, field.related_model, field, path, urlpatterns, debug)
            elif isinstance(field, ManyToOneRel):
                _register(recurse, field.related_model, field, path, urlpatterns, debug)
            else:
                urlpatterns.append(url('^%s/%s/$' % (path, field.name), unrest, kwargs={
                    'model': name, 'field': field.name
                }))
                if debug:
                    print('UnReSTFul API: Registered Model "%s.%s" URL: "^%s/%s/$"..' % (
                        name, field.name, path, field.name
                    ))
        del fields

# EOF
