import pathlib
import argparse
import logging
import io

import arrow
import pyhocon
import ruamel.yaml

from cloud_init_utils import constants
from cloud_init_utils.model import HoconTypesEnum, ConfigFileSettings
from cloud_init_utils.model import CloudInitFileToWrite, CloudInitSettings, ConfigFileSettings

class ArrowLoggingFormatter(logging.Formatter):
    ''' logging.Formatter subclass that uses arrow, that formats the timestamp
    to the local timezone (but its in ISO format)
    '''

    def formatTime(self, record, datefmt=None):
        return arrow.get("{}".format(record.created), "X").to("local").isoformat()



def get_yaml_file_string_from_dict(input_dict:dict) -> str:

    yaml_string_io = io.StringIO()

    # get the 'handle' to the YAML parser/dumper, it seems like this
    # is basically like a handle in the C sense, it doesn't really handle any
    # state itself but i just give it instances to the stuff i'm dumping
    # you need `rt` (round trip) to make it preserve comments
    yaml_handle = ruamel.yaml.YAML(typ="rt")

    comment_mark = ruamel.yaml.error.CommentMark(column=0)
    cloud_config_comment_token  = ruamel.yaml.tokens.CommentToken("#cloud-config\n", comment_mark, None)

    # basically a regular dictionary that we will add to , that supports comments
    yaml_dictionary = ruamel.yaml.comments.CommentedMap(input_dict)

    # add the comment
    # we can't call the handly method on `ruamel.yaml.comments.CommentedMap`: `yaml_set_start_comment()` because it
    # adds a space between the `#` and the rest of the comment, and we need it to be WITHOUT a space, see the examples
    # for cloudinit: https://cloudinit.readthedocs.io/en/latest/topics/examples.html
    # so we have to hack together some thing to add a comment without a space
    # see https://sourceforge.net/p/ruamel-yaml/tickets/371/
    yaml_dictionary._yaml_get_pre_comment().append(cloud_config_comment_token)

    # TODO: maybe write the input_dict or some other identifying info to the end of line comment of the yaml
    # so we can tell which yaml goes to which instance without decompressing the gzip script and looking at the
    # variables

    # then write the commented map with the comment to the StringIO
    yaml_handle.dump(yaml_dictionary, yaml_string_io)

    return yaml_string_io.getvalue()


def _get_key_or_throw(conf_obj, key, type_:HoconTypesEnum):
    '''
    returns the value at the hocon config for the given key, or throws
    an exception

    @param conf_obj the config object (probably the root object)
    @param key - the key we want from the conf_obj
    @param type_ - a member of HoconTypesEnum of what type we want are expecting
    out of the config
    '''

    try:
        if type_ == HoconTypesEnum.STRING:
            return conf_obj.get_string(key)
        elif type_ == HoconTypesEnum.INT:
            return conf_obj.get_int(key)
        elif type_ == HoconTypesEnum.FLOAT:
            return conf_obj.get_float(key)
        elif type_ == HoconTypesEnum.LIST:
            return conf_obj.get_list(key)
        elif type_ == HoconTypesEnum.BOOLEAN:
            return conf_obj.get_bool(key)
        elif type_ == HoconTypesEnum.CONFIG:
            return conf_obj.get_config(key)
        elif type_ == HoconTypesEnum.ANY:
            return conf_obj.get(key)
        else:
            raise Exception(f"unknown HoconTypesEnum type `{type_}`")
    except Exception as e:
        raise Exception(
            f"Unable to get the key `{key}`, using the type `{type_}` from the config because of: `{e}`") from e

def isFileType(strict=True):
    def _isFileType(filePath):
        ''' see if the file path given to us by argparse is a file
        @param filePath - the filepath we get from argparse
        @return the filepath as a pathlib.Path() if it is a file, else we raise a ArgumentTypeError'''

        path_maybe = pathlib.Path(filePath)
        path_resolved = None

        # try and resolve the path
        try:
            path_resolved = path_maybe.resolve(strict=strict).expanduser()

        except Exception as e:
            raise argparse.ArgumentTypeError("Failed to parse `{}` as a path: `{}`".format(filePath, e))

        # double check to see if its a file
        if strict:
            if not path_resolved.is_file():
                raise argparse.ArgumentTypeError("The path `{}` is not a file!".format(path_resolved))

        return path_resolved
    return _isFileType

def isDirectoryType(filePath):
    ''' see if the file path given to us by argparse is a directory
    @param filePath - the filepath we get from argparse
    @return the filepath as a pathlib.Path() if it is a directory, else we raise a ArgumentTypeError'''

    path_maybe = pathlib.Path(filePath)
    path_resolved = None

    # try and resolve the path
    try:
        path_resolved = path_maybe.resolve(strict=True).expanduser()

    except Exception as e:
        raise argparse.ArgumentTypeError("Failed to parse `{}` as a path: `{}`".format(filePath, e))

    # double check to see if its a file
    if not path_resolved.is_dir():
        raise argparse.ArgumentTypeError("The path `{}` is not a file!".format(path_resolved))

    return path_resolved


def hocon_config_file_type(stringArg):
    ''' argparse type method that returns a pyhocon Config object
    or raises an argparse.ArgumentTypeError if this file doesn't exist

    @param stringArg - the argument given to us by argparse
    @return a dict like object containing the configuration or raises ArgumentTypeError
    '''

    resolved_path = pathlib.Path(stringArg).expanduser().resolve()
    if not resolved_path.exists:
        raise argparse.ArgumentTypeError("The path {} doesn't exist!".format(resolved_path))

    conf = None
    try:
        conf = pyhocon.ConfigFactory.parse_file(str(resolved_path))
    except Exception as e:
        raise argparse.ArgumentTypeError(
            "Failed to parse the file `{}` as a HOCON file due to an exception: `{}`".format(resolved_path, e))

    return conf

def parse_config(config_obj) -> ConfigFileSettings:
    ''' parse the config into our settings object

    '''


    top_level_key = f"{constants.HOCON_CONFIG_KEY_TOP_LEVEL_GROUP}"
    top_level_obj = _get_key_or_throw(config_obj, top_level_key, HoconTypesEnum.CONFIG)


    cloud_init_settings_key = f"{top_level_key}.{constants.HOCON_CONFIG_KEY_CLOUD_INIT_SETTINGS_GROUP}"

    username_key = f"{cloud_init_settings_key}.{constants.HOCON_CONFIG_KEY_CLOUD_INIT_USER_NAME}"
    username = _get_key_or_throw(config_obj, username_key, HoconTypesEnum.STRING)

    password_key = f"{cloud_init_settings_key}.{constants.HOCON_CONFIG_KEY_CLOUD_INIT_PASSWORD}"
    password = _get_key_or_throw(config_obj, password_key, HoconTypesEnum.STRING)

    ssh_auths_key = f"{cloud_init_settings_key}.{constants.HOCON_CONFIG_KEY_CLOUD_INIT_SSH_AUTH_KEYS}"
    ssh_auths_list = _get_key_or_throw(config_obj, ssh_auths_key, HoconTypesEnum.LIST)

    byobu_key = f"{cloud_init_settings_key}.{constants.HOCON_CONFIG_KEY_CLOUD_INIT_BYOBU_ENABLE}"
    byobu_enable = _get_key_or_throw(config_obj, byobu_key, HoconTypesEnum.BOOLEAN)

    install_list_key = f"{cloud_init_settings_key}.{constants.HOCON_CONFIG_KEY_CLOUD_INIT_PACKAGES_TO_INSTALL_LIST}"
    to_install_list = _get_key_or_throw(config_obj, install_list_key, HoconTypesEnum.LIST)


    files_to_write_key = f"{cloud_init_settings_key}.{constants.HOCON_CONFIG_KEY_CLOUD_INIT_FILES_TO_WRITE_LIST}"
    files_to_write_list = _get_key_or_throw(config_obj, files_to_write_key, HoconTypesEnum.LIST)


    list_of_files_to_write_objs = []

    for iter_file_to_write_config_obj in files_to_write_list:

        file_path_key = f"{constants.HOCON_CONFIG_KEY_CLOUD_INIT_FILES_TO_WRITE_FILE_PATH}"
        file_path = _get_key_or_throw(iter_file_to_write_config_obj, file_path_key, HoconTypesEnum.STRING)

        owner_username_key =  f"{constants.HOCON_CONFIG_KEY_CLOUD_INIT_FILES_TO_WRITE_OWNER_USERNAME}"
        owner_username = _get_key_or_throw(iter_file_to_write_config_obj, owner_username_key, HoconTypesEnum.STRING)

        owner_group_key =  f"{constants.HOCON_CONFIG_KEY_CLOUD_INIT_FILES_TO_WRITE_OWNER_GROUP}"
        owner_group = _get_key_or_throw(iter_file_to_write_config_obj, owner_group_key, HoconTypesEnum.STRING)

        permission_octal_key =  f"{constants.HOCON_CONFIG_KEY_CLOUD_INIT_FILES_TO_WRITE_PERMISSION_OCTAL}"
        permission_octal = _get_key_or_throw(iter_file_to_write_config_obj, permission_octal_key, HoconTypesEnum.STRING)

        payload_is_base64_key =  f"{constants.HOCON_CONFIG_KEY_CLOUD_INIT_FILES_TO_WRITE_PAYLOAD_IS_BASE64}"
        payload_is_base64 = _get_key_or_throw(iter_file_to_write_config_obj, payload_is_base64_key, HoconTypesEnum.BOOLEAN)

        payload_content_key =  f"{constants.HOCON_CONFIG_KEY_CLOUD_INIT_FILES_TO_WRITE_PAYLOAD_CONTENT}"
        payload_content = _get_key_or_throw(iter_file_to_write_config_obj, payload_content_key, HoconTypesEnum.STRING)


        new_obj = CloudInitFileToWrite(
            file_path=file_path,
            owner_username=owner_username,
            owner_group=owner_group,
            permission_octal=permission_octal,
            payload_is_base64=payload_is_base64,
            payload_content=payload_content)

        list_of_files_to_write_objs.append(new_obj)


    cloud_init_settings = CloudInitSettings(
        user_name=username,
        ssh_authorized_keys=ssh_auths_list,
        password=password,
        packages_to_install=to_install_list,
        byobu_enable=byobu_enable,
        files_to_write=list_of_files_to_write_objs)


    config_settings = ConfigFileSettings(
        cloud_init_settings=cloud_init_settings)

    return config_settings

