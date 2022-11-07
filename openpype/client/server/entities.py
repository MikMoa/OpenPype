import collections

from .server_api import get_server_api_connection
from .conversion_utils import (
    project_fields_v3_to_v4,
    convert_v4_project_to_v3,

    folder_fields_v3_to_v4,
    convert_v4_folder_to_v3,

    subset_fields_v3_to_v4,
    convert_v4_subset_to_v3,

    version_fields_v3_to_v4,
    convert_v4_version_to_v3,

    representation_fields_v3_to_v4,
    convert_v4_representation_to_v3,
)


def get_projects(active=True, inactive=False, library=None, fields=None):
    if not active and not inactive:
        return []

    if active and inactive:
        active = None
    elif active:
        active = True
    elif inactive:
        active = False

    fields = project_fields_v3_to_v4(fields)
    con = get_server_api_connection()
    for project in con.get_projects(active, library, fields):
        yield convert_v4_project_to_v3(project)


def get_project(project_name, active=True, inactive=False, fields=None):
    # Skip if both are disabled
    fields = project_fields_v3_to_v4(fields)
    con = get_server_api_connection()
    return convert_v4_project_to_v3(
        con.get_project(project_name, fields=fields)
    )


def get_whole_project(*args, **kwargs):
    raise NotImplementedError("'get_whole_project' not implemented")


def _get_subsets(
    project_name,
    subset_ids=None,
    subset_names=None,
    folder_ids=None,
    names_by_folder_ids=None,
    archived=False,
    fields=None
):
    # Convert fields and add minimum required fields
    fields = subset_fields_v3_to_v4(fields)
    if fields is not None:
        for key in (
            "id",
            "active"
        ):
            fields.add(key)

    con = get_server_api_connection()
    for subset in con.get_subsets(
        project_name,
        subset_ids,
        subset_names,
        folder_ids,
        names_by_folder_ids,
        archived,
        fields
    ):
        yield convert_v4_subset_to_v3(subset)


def _get_versions(
    project_name,
    version_ids=None,
    subset_ids=None,
    versions=None,
    hero=True,
    standard=True,
    latest=None,
    fields=None
):
    fields = version_fields_v3_to_v4(fields)

    con = get_server_api_connection()

    # Make sure 'subsetId' and 'version' are available when hero versions
    #   are queried
    if fields and hero:
        fields = set(fields)
        fields |= {"subsetId", "version"}

    queried_versions = con.get_versions(
        project_name,
        version_ids,
        subset_ids,
        versions,
        hero,
        standard,
        latest,
        fields=fields
    )

    versions = []
    hero_versions = []
    for version in queried_versions:
        if version["version"] < 0:
            hero_versions.append(version)
        else:
            versions.append(convert_v4_version_to_v3(version))

    if hero_versions:
        subset_ids = set()
        versions_nums = set()
        for hero_version in hero_versions:
            versions_nums.add(abs(hero_version["version"]))
            subset_ids.add(hero_version["subsetId"])

        hero_eq_versions = con.get_versions(
            project_name,
            subset_ids=subset_ids,
            versions=versions_nums,
            hero=False,
            fields=["id", "version", "subsetId"]
        )
        hero_eq_by_subset_id = collections.defaultdict(list)
        for version in hero_eq_versions:
            hero_eq_by_subset_id[version["subsetId"]].append(version)

        for hero_version in hero_versions:
            abs_version = abs(hero_version["version"])
            subset_id = hero_version["subsetId"]
            version_id = None
            for version in hero_eq_by_subset_id.get(subset_id, []):
                if version["version"] == abs_version:
                    version_id = version["id"]
                    break
            conv_hero = convert_v4_version_to_v3(hero_version)
            conv_hero["version_id"] = version_id

    return versions


def get_asset_by_id(project_name, asset_id, fields=None):
    assets = get_assets(
        project_name, asset_ids=[asset_id], fields=fields
    )
    for asset in assets:
        return asset
    return None


def get_asset_by_name(project_name, asset_name, fields=None):
    assets = get_assets(
        project_name, asset_names=[asset_name], fields=fields
    )
    for asset in assets:
        return asset
    return None


def get_assets(
    project_name,
    asset_ids=None,
    asset_names=None,
    parent_ids=None,
    archived=False,
    fields=None
):
    if not project_name:
        return []

    active = True
    if archived:
        active = False

    con = get_server_api_connection()
    fields = folder_fields_v3_to_v4(fields)
    kwargs = dict(
        folder_ids=asset_ids,
        folder_names=asset_names,
        parent_ids=parent_ids,
        active=active,
        fields=fields
    )

    if "tasks" in fields:
        folders = con.get_folders_with_tasks(project_name, **kwargs)

    else:
        folders = con.get_folders(project_name, **kwargs)

    for folder in folders:
        yield convert_v4_folder_to_v3(folder, project_name)


def get_archived_assets(*args, **kwargs):
    raise NotImplementedError("'get_archived_assets' not implemented")


def get_asset_ids_with_subsets(project_name, asset_ids=None):
    con = get_server_api_connection()
    return con.get_asset_ids_with_subsets(project_name, asset_ids)


def get_subset_by_id(project_name, subset_id, fields=None):
    subsets = get_subsets(
        project_name, subset_ids=[subset_id], fields=fields
    )
    for subset in subsets:
        return subset
    return None


def get_subset_by_name(project_name, subset_name, asset_id, fields=None):
    subsets = get_subsets(
        project_name,
        subset_names=[subset_name],
        asset_ids=[asset_id],
        fields=fields
    )
    for subset in subsets:
        return subset
    return None


def get_subsets(
    project_name,
    subset_ids=None,
    subset_names=None,
    asset_ids=None,
    names_by_asset_ids=None,
    archived=False,
    fields=None
):
    return _get_subsets(
        project_name,
        subset_ids,
        subset_names,
        asset_ids,
        names_by_asset_ids,
        archived,
        fields=fields
    )


def get_subset_families(project_name, subset_ids=None):
    con = get_server_api_connection()
    return con.get_subset_families(project_name, subset_ids)


def get_version_by_id(project_name, version_id, fields=None):
    versions = get_versions(
        project_name,
        version_ids=[version_id],
        fields=fields,
        hero=True
    )
    for version in versions:
        return version
    return None


def get_version_by_name(project_name, version, subset_id, fields=None):
    versions = get_versions(
        project_name,
        subset_ids=[subset_id],
        versions=[version],
        fields=fields
    )
    for version in versions:
        return version
    return None


def get_versions(
    project_name,
    version_ids=None,
    subset_ids=None,
    versions=None,
    hero=False,
    fields=None
):
    return _get_versions(
        project_name,
        version_ids,
        subset_ids,
        versions,
        hero=hero,
        standard=True,
        fields=fields
    )


def get_hero_version_by_id(project_name, version_id, fields=None):
    versions = get_hero_versions(
        project_name,
        version_ids=[version_id],
        fields=fields
    )
    for version in versions:
        return version
    return None


def get_hero_version_by_subset_id(
    project_name, subset_id, fields=None
):
    versions = get_hero_versions(
        project_name,
        subset_ids=[subset_id],
        fields=fields
    )
    for version in versions:
        return version
    return None


def get_hero_versions(
    project_name, subset_ids=None, version_ids=None, fields=None
):
    return _get_versions(
        project_name,
        version_ids=version_ids,
        subset_ids=subset_ids,
        hero=True,
        standard=False,
        fields=fields
    )


def get_last_versions(project_name, subset_ids, fields=None):
    versions = _get_versions(
        project_name,
        subset_ids=subset_ids,
        latest=True,
        fields=fields
    )
    return {
        version["parent"]: version
        for version in versions
    }


def get_last_version_by_subset_id(project_name, subset_id, fields=None):
    versions = _get_versions(
        project_name,
        subset_ids=[subset_id],
        latest=True,
        fields=fields
    )
    if not versions:
        return versions[0]
    return None


def get_last_version_by_subset_name(
    project_name,
    subset_name,
    asset_id=None,
    asset_name=None,
    fields=None
):
    if not asset_id and not asset_name:
        return None

    if not asset_id:
        asset = get_asset_by_name(
            project_name, asset_name, fields=["_id"]
        )
        if not asset:
            return None
        asset_id = asset["_id"]

    subset = get_subset_by_name(
        project_name, subset_name, asset_id, fields=["_id"]
    )
    if not subset:
        return None
    return get_last_version_by_subset_id(
        project_name, subset["id"], fields=fields
    )


def get_output_link_versions(*args, **kwargs):
    raise NotImplementedError("'get_output_link_versions' not implemented")


def version_is_latest(project_name, version_id):
    con = get_server_api_connection()
    return con.version_is_latest(project_name, version_id)


def get_representation_by_id(project_name, representation_id, fields=None):
    representations = get_representations(
        project_name,
        representation_ids=[representation_id],
        fields=fields
    )
    for representation in representations:
        return representation
    return None


def get_representation_by_name(
    project_name, representation_name, version_id, fields=None
):
    representations = get_representations(
        project_name,
        representation_names=[representation_name],
        version_ids=[version_id],
        fields=fields
    )
    for representation in representations:
        return representation
    return None


def get_representations(
    project_name,
    representation_ids=None,
    representation_names=None,
    version_ids=None,
    context_filters=None,
    names_by_version_ids=None,
    archived=False,
    standard=True,
    fields=None
):
    if context_filters is not None:
        # TODO should we add the support?
        # - there was ability to fitler using regex
        raise ValueError("OP v4 can't filter by representation context.")

    if not archived and not standard:
        return []

    if archived and not standard:
        active = False
    elif not archived and standard:
        active = True
    else:
        active = None

    fields = representation_fields_v3_to_v4(fields)
    con = get_server_api_connection()
    representations = con.get_representations(
        project_name,
        representation_ids,
        representation_names,
        version_ids,
        names_by_version_ids,
        active,
        fields=fields
    )
    for representation in representations:
        yield convert_v4_representation_to_v3(representation)


def get_representation_parents(project_name, representation):
    if not representation:
        return None

    repre_id = representation["_id"]
    parents_by_repre_id = get_representations_parents(
        project_name, [representation]
    )
    return parents_by_repre_id[repre_id]


def get_representations_parents(project_name, representations):
    repre_ids = {
        repre["_id"]
        for repre in representations
    }
    con = get_server_api_connection()
    parents = con.get_representations_parents(project_name, repre_ids)
    folder_ids = set()
    for parents in parents.values():
        folder_ids.add(parents[2]["id"])

    tasks_by_folder_id = {}

    new_parents = {}
    for repre_id, parents in parents.items():
        version, subset, folder, project = parents
        folder_tasks = tasks_by_folder_id.get(folder["id"]) or {}
        folder["tasks"] = folder_tasks
        new_parents[repre_id] = (
            convert_v4_version_to_v3(version),
            convert_v4_subset_to_v3(subset),
            convert_v4_folder_to_v3(folder, project_name),
            project
        )
    return new_parents


def get_archived_representations(*args, **kwargs):
    raise NotImplementedError("'get_archived_representations' not implemented")


def get_thumbnail(project_name, thumbnail_id, fields=None):
    # TODO thumbnails are handled in a different way
    return None


def get_thumbnails(project_name, thumbnail_ids, fields=None):
    # TODO thumbnails are handled in a different way
    return []


def get_thumbnail_id_from_source(project_name, src_type, src_id):
    """Receive thumbnail id from source entity.

    Args:
        project_name (str): Name of project where to look for queried entities.
        src_type (str): Type of source entity ('asset', 'version').
        src_id (Union[str, ObjectId]): Id of source entity.

    Returns:
        ObjectId: Thumbnail id assigned to entity.
        None: If Source entity does not have any thumbnail id assigned.
    """

    if not src_type or not src_id:
        return None

    if src_type == "subset":
        subset = get_subset_by_id(
            project_name, src_id, fields=["data.thumbnail_id"]
        ) or {}
        return subset.get("data", {}).get("thumbnail_id")

    if src_type == "subset":
        subset = get_asset_by_id(
            project_name, src_id, fields=["data.thumbnail_id"]
        ) or {}
        return subset.get("data", {}).get("thumbnail_id")

    return None


def get_workfile_info(
    project_name, asset_id, task_name, filename, fields=None
):
    # TODO workfile info not implemented in v4 yet
    return None