import json
from dataclasses import dataclass

import requests


@dataclass
class ReleaseData:
    link: str
    body: str
    version: str
    link_pypi: str

    def __repr__(self) -> str:
        rep = f"## [{self.version}]({self.link})\n"
        body_ = "## " + "## ".join(self.body.split("## ")[1:])
        body_ = body_.replace("# ", "## ")
        rep += body_
        rep += "\n\n----------------------------\n"
        return rep


def main() -> None:
    """
    curl -L \
    -H "Accept: application/vnd.github+json" \
    -H "Authorization: Bearer <YOUR-TOKEN>" \
    -H "X-GitHub-Api-Version: 2022-11-28" \
    https://api.github.com/repos/OWNER/REPO/releases
    """
    data_ = requests.get(
        "https://api.github.com/repos/kschweiger/track_analyzer/releases",
        headers={
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )

    if data_.status_code != 200:
        print("Can not fetch release data: %s" % data_.content)
        exit(1)

    data = json.loads(data_.content)

    data_for_md = [
        "For a more detailed changelog see [CHANGELOG](https://github.com/kschweiger/track_analyzer/blob/main/CHANGELOG.md) on GitHub"
    ]

    for release in data:
        data_for_md.append(
            ReleaseData(
                link=release["html_url"],
                body=release["body"],
                version=release["name"],
                link_pypi=f"https://pypi.org/project/geo_track_analyzer/{release['name']}/",
            )
        )

    with open("docs/changelog.md", "w") as f:
        f.write("\n".join(map(str, data_for_md)))


if __name__ == "__main__":
    main()
