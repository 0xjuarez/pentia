from typing import Dict, List


class DecisionEngine:
    DEFAULT_RULES = {
        "smb": ["enum4linux"],
        "kerberos": ["kerbrute"],
        "http": ["ffuf", "nuclei"],
        "wordpress": ["wpscan"],
        "ad": ["bloodhound"],
    }

    @staticmethod
    def normalize_service_line(line: str) -> str:
        return line.strip().lower()

    @classmethod
    def infer_services(cls, nmap_output: str) -> List[str]:
        services = []
        for line in nmap_output.splitlines():
            normalized = cls.normalize_service_line(line)
            if "http" in normalized or "80/tcp" in normalized:
                services.append("http")
            if "smb" in normalized or "445/tcp" in normalized:
                services.append("smb")
            if "kerberos" in normalized or "88/tcp" in normalized:
                services.append("kerberos")
            if "ldap" in normalized or "389/tcp" in normalized:
                services.append("ldap")
            if "wordpress" in normalized or "wp" in normalized:
                services.append("wordpress")
            if "microsoft-ds" in normalized:
                services.append("ad")
        return list(dict.fromkeys(services))

    @classmethod
    def choose_actions(cls, services: List[str]) -> List[str]:
        actions = []
        for service in services:
            actions.extend(cls.DEFAULT_RULES.get(service, []))
        return list(dict.fromkeys(actions))

    @classmethod
    def decide(cls, nmap_output: str) -> Dict[str, List[str]]:
        services = cls.infer_services(nmap_output)
        return {
            "services": services,
            "actions": cls.choose_actions(services),
        }
