import pathlib
import typing
import enum
import base64
import gzip

import attr



@attr.s(auto_attribs=True, frozen=True, kw_only=True)
class FileToWrite:


    file_path:pathlib.Path = attr.ib()
    owner_username:str = attr.ib()
    owner_group:str = attr.ib()
    permission_octal:str = attr.ib()


    # if true, we won't base64 the payload
    payload_is_base64:bool = attr.ib()

    payload_content:bytes = attr.ib()

    def format_as_yaml_dict(self):
        '''
        formats this object in a suitable manner
        to be serialized as part of a cloud-init YAML file


        @return a dictioanry, suitable to be converted to yaml
        '''
        final_dict = dict()

        final_dict["path"] = self.file_path
        final_dict["owner"] = f"{self.owner_username}:{self.owner_group}"
        final_dict["permissions"] = self.permission_octal

        # we need to gzip the content, however the user might pass it in
        # as a string or as a base64 string (in our HOCON config) so we need
        # to get the raw bytes of it so we can gzip it

        raw_content_bytes =  None
        if self.payload_is_base64:

            # un-base64 the content

            try:

                raw_content_bytes = base64.b64decode(self.payload_content.encode("utf-8"))

            except Exception as e:
                self.logger.exception("Caught exception when decoding the payload content as base64! Self: `%s`", self)
                raise e
        else:

            # don't need to do anything since its just the raw content already
            raw_content_bytes = self.payload_content.encode("utf-8")


        # now gzip the content
        compressed_content_bytes = gzip.compress(raw_content_bytes)

        final_dict["encoding"] = "gzip"
        final_dict["content"] = compressed_content_bytes

        return final_dict


@attr.s(auto_attribs=True, frozen=True, kw_only=True)
class BootstrapScriptSettings:

    root_folder:pathlib.Path = attr.ib()
    zip_url:str = attr.ib()
    zip_root_folder:str = attr.ib()
    command_line:typing.Sequence[str] = attr.ib()
    acceptable_status_codes:typing.Sequence[int] = attr.ib()
    files_to_write:typing.Sequence[FileToWrite] = attr.ib()


@attr.s(auto_attribs=True, frozen=True, kw_only=True)
class CloudInitSettings:


    user_name:str = attr.ib()
    ssh_authorized_keys:list = attr.ib()
    password:str = attr.ib()
    packages_to_install:list = attr.ib()
    byobu_enable:bool = attr.ib()
    files_to_write:typing.Sequence[FileToWrite] = attr.ib()


    def format_as_yaml_dict(self) -> dict:
        '''
        formats this object in a suitable manner
        to be serialized as a cloud-init YAML file


        @return a dictioanry, suitable to be converted to yaml
        '''


        final_dict = dict()

        users_list = []
        users_list.append("default")
        default_user_obj = {
            "name": self.user_name,
            "groups": "admin",
            "shell": "/bin/bash",
            "sudo": ['ALL=(ALL) NOPASSWD:ALL'],
            "ssh-authorized-keys": self.ssh_authorized_keys,
        }

        users_list.append(default_user_obj)
        final_dict["users"] = users_list


        chpasswd_dict = {
            "list":  [f"{self.user_name}:{self.password}"],
            "expire": False
        }
        final_dict["chpasswd"] = chpasswd_dict

        final_dict["package_update"] = True
        final_dict["package_upgrade"] = True
        final_dict["packages"] = self.packages_to_install
        final_dict["byobu_by_default"] = "enable" if self.byobu_enable else "disable"

        write_files_list = [iter_file.format_as_yaml_dict() for iter_file in self.files_to_write]
        final_dict["write_files"] = write_files_list


        return final_dict



@attr.s(auto_attribs=True, frozen=True, kw_only=True)
class ConfigFileSettings:


    cloud_init_settings:CloudInitSettings = attr.ib()
    bootstrap_script_settings:BootstrapScriptSettings = attr.ib()





class HoconTypesEnum(enum.Enum):
    STRING = "string"
    INT = "int"
    FLOAT = "float"
    LIST = "list"
    BOOLEAN = "boolean"
    CONFIG = "config"
    ANY = "any"
