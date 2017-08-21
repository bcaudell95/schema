from functools import wraps
from wrapt import ObjectProxy
from schema import Schema, And, Or


class ValidatedMeta(type):
    def __new__(mcs, name, bases, nmspc):
        assert '__schema__' in nmspc
        schema = nmspc['__schema__']
        assert any([issubclass(type(schema), cls) for cls in [Schema, And, Or]])

        if '__name__' in nmspc:
            name = nmspc['__name__']

        assert '__init__' in nmspc
        old_init = nmspc['__init__']

        # wraps here ensures that underlying metadata of the init method are preserved
        @wraps(old_init)
        def patched(*args):
            assert len(args) == 2
            args_list = list(args)
            args_list[1] = schema.validate(args_list[1])

            old_init(*args_list)

        nmspc['__init__'] = patched

        return super(ValidatedMeta, mcs).__new__(mcs, name, bases, nmspc)

    def __str__(self):
        return "<schema-validated data: {}>".format(self.__name__)


def validated_by(schema: (Schema, And, Or), name='ValidatedData') -> type:
    """
    This method spawns a class used to validate and wrap data.
    While this method/class can be used for this data validation, its main utility is for type hinting of function
        parameters taking complex data structures.
    See test code for examples on this functionality.

    :param schema: The schema used for validation.
    :param name: A name provided to the class being created.
    :return: A class for validation and wrapping of input data.
    """

    class GenericWrappedData(ObjectProxy, metaclass=ValidatedMeta):
        """
        This class serves as a wrapper for schema-validated data.
        Data passed into the constructor will be validated by the provided schema, and the result of .validate will
            be set onto this object's .data member variable.
        Because this object inherits ObjectProxy, this wrapper will be near-completely transparent.  All arithmetic,
            subscripting, and mutation operations on this object will be passed down to the internal object.
            Thus, users of this object oftentimes don't need to be aware of the wrapper at all.
        Users may access the schema used to validate the data by accessing the .__schema__ member variable.
        """

        # This will be used by the metaclass to override the "GenericWrappedData" name.
        __name__ = name
        __schema__ = schema

        def __init__(self, validated_data):
            super().__init__(validated_data)

    return GenericWrappedData
