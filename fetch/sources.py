from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass(frozen=True)
class ConferenceConfig:
    alias: str
    name: str
    stream_id: str
    allowed_venues: Tuple[str, ...]


CONFERENCES: Dict[str, ConferenceConfig] = {
    "cvpr": ConferenceConfig("cvpr", "CVPR", "conf/cvpr", ("CVPR",)),
    "iccv": ConferenceConfig("iccv", "ICCV", "conf/iccv", ("ICCV",)),
    "eccv": ConferenceConfig("eccv", "ECCV", "conf/eccv", ("ECCV",)),
    "nips": ConferenceConfig("nips", "NeurIPS", "conf/nips", ("NeurIPS", "NIPS")),
    "icml": ConferenceConfig("icml", "ICML", "conf/icml", ("ICML",)),
    "iclr": ConferenceConfig("iclr", "ICLR", "conf/iclr", ("ICLR",)),
    "acl": ConferenceConfig("acl", "ACL", "conf/acl", ("ACL", "ACL (1)", "ACL (2)")),
    "emnlp": ConferenceConfig("emnlp", "EMNLP", "conf/emnlp", ("EMNLP", "EMNLP (1)", "EMNLP (2)")),
    "naacl": ConferenceConfig("naacl", "NAACL", "conf/naacl", ("NAACL",)),
    "aaai": ConferenceConfig("aaai", "AAAI", "conf/aaai", ("AAAI",)),
    "ijcai": ConferenceConfig("ijcai", "IJCAI", "conf/ijcai", ("IJCAI",)),
    "kdd": ConferenceConfig("kdd", "KDD", "conf/kdd", ("KDD",)),
    "www": ConferenceConfig("www", "WWW", "conf/www", ("WWW", "The Web Conference")),
    "sigir": ConferenceConfig("sigir", "SIGIR", "conf/sigir", ("SIGIR",)),
    "sigmod": ConferenceConfig("sigmod", "SIGMOD", "conf/sigmod", ("SIGMOD Conference", "SIGMOD")),
    "vldb": ConferenceConfig("vldb", "VLDB", "journals/pvldb", ("PVLDB", "Proc. VLDB Endow.")),
    "icse": ConferenceConfig("icse", "ICSE", "conf/icse", ("ICSE",)),
    "fse": ConferenceConfig("fse", "FSE", "conf/sigsoft", ("ESEC/SIGSOFT FSE", "FSE")),
    "sosp": ConferenceConfig("sosp", "SOSP", "conf/sosp", ("SOSP",)),
    "osdi": ConferenceConfig("osdi", "OSDI", "conf/osdi", ("OSDI",)),
    "nsdi": ConferenceConfig("nsdi", "NSDI", "conf/nsdi", ("NSDI",)),
    "sigcomm": ConferenceConfig("sigcomm", "SIGCOMM", "conf/sigcomm", ("SIGCOMM",)),
    "chi": ConferenceConfig("chi", "CHI", "conf/chi", ("CHI",)),
    "mm": ConferenceConfig("mm", "ACM MM", "conf/mm", ("ACM Multimedia", "MM")),
}
