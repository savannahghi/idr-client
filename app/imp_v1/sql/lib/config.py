from abc import ABCMeta, abstractmethod
from collections.abc import Mapping
from typing import Final, TypedDict

from attrs import field, frozen
from sqlalchemy.engine.url import URL, make_url

from app.lib.config import ImproperlyConfiguredError, SettingInitializer

# =============================================================================
# TYPES
# =============================================================================


class _DBInstanceConfigMapping(TypedDict, total=False):
    db_name: str
    driver: str
    host: str
    password: str
    port: int
    username: str
    url: str


# =============================================================================
# CONSTANTS
# =============================================================================

_DB_INSTANCES_CONFIG_KEY: Final[str] = "DATABASE_INSTANCES"


# =============================================================================
# HELPERS
# =============================================================================


class DBInstanceConfig(metaclass=ABCMeta):
    @property
    @abstractmethod
    def db_url(self) -> URL:
        ...


@frozen
class DBInstanceConfigURLConfig(DBInstanceConfig):
    url_string: str = field(repr=False)
    _db_url: URL = field(init=False)

    def __attrs_post_init__(self) -> None:
        object.__setattr__(self, "_db_url", make_url(self.url_string))

    @property
    def db_url(self) -> URL:
        return self._db_url


@frozen
class DBInstanceURLComponentsConfig(DBInstanceConfig):
    driver: str = field()
    db_name: str | None = field(default=None, kw_only=True)
    host: str | None = field(default=None, kw_only=True)
    password: str | None = field(default=None, kw_only=True, repr=False)
    port: int | None = field(default=None, kw_only=True)
    username: str | None = field(default=None, kw_only=True)
    _db_url: URL = field(init=False)

    def __attrs_post_init__(self) -> None:
        object.__setattr__(
            self,
            "_db_url",
            URL.create(
                drivername=self.driver,
                database=self.db_name,
                host=self.host,
                password=self.password,
                port=self.port,
                username=self.username,
            ),
        )

    @property
    def db_url(self) -> URL:
        return self._db_url


# =============================================================================
# DB INSTANCES INITIALIZERS
# =============================================================================


class DBInstancesInitializer(SettingInitializer):
    @property
    def has_secrets(self) -> bool:
        return True

    @property
    def setting(self) -> str:
        return _DB_INSTANCES_CONFIG_KEY

    def execute(
        self,
        an_input: Mapping[str, _DBInstanceConfigMapping] | None,
    ) -> Mapping[str, DBInstanceConfig]:
        return (
            {}
            if an_input is None
            else dict(
                map(
                    self._db_instance_config_mapping_to_config_instance,
                    an_input.items(),
                ),
            )
        )

    @staticmethod
    def _db_instance_config_mapping_to_config_instance(
        _raw_config: tuple[str, _DBInstanceConfigMapping],
    ) -> tuple[str, DBInstanceConfig]:
        _db_instance_name: str = _raw_config[0]
        _db_instance_config_mapping: _DBInstanceConfigMapping
        _db_instance_config_mapping = _raw_config[1]
        _URLConf = DBInstanceConfigURLConfig  # noqa: N806
        _CompsConf = DBInstanceURLComponentsConfig  # noqa: N806
        match _db_instance_config_mapping:
            case {"url": url}:
                return _db_instance_name, _URLConf(url_string=url)
            case {"driver": driver, **rest}:
                return _db_instance_name, _CompsConf(driver=driver, **rest)
            case _:
                _err_message: str = (
                    'Invalid database instance configuration for instance "{}"'
                    "The instance configuration should at the very least have "
                    'a "driver" or "url" configuration option.'.format(
                        _db_instance_name,
                    )
                )
                raise ImproperlyConfiguredError(message=_err_message)
