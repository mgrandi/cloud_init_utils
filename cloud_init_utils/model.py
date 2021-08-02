import pathlib
import typing
import enum

import attr






@attr.s(auto_attribs=True, frozen=True, kw_only=True)
class CloudInitFileToWrite:

    file_path:pathlib.Path = attr.ib()
    owner_username:str = attr.ib()
    owner_group:str = attr.ib()
    permission_octal:str = attr.ib()


    # if true, we won't base64 the payload
    payload_is_base64:bool = attr.ib()

    payload_content:bytes = attr.ib()


@attr.s(auto_attribs=True, frozen=True, kw_only=True)
class CloudInitSettings:


    user_name:str = attr.ib()
    ssh_authorized_key:str = attr.ib()
    password:str = attr.ib()
    packages_to_install_list:list = attr.ib()
    byobu_enable:bool = attr.ib()
    files_to_write:typing.Sequence[CloudInitFileToWrite] = attr.ib()


@attr.s(auto_attribs=True, frozen=True, kw_only=True)
class ConfigFileSettings:


    cloud_init_settings:CloudInitSettings = attr.ib()





class HoconTypesEnum(enum.Enum):
    STRING = "string"
    INT = "int"
    FLOAT = "float"
    LIST = "list"
    BOOLEAN = "boolean"
    CONFIG = "config"
    ANY = "any"
