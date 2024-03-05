lea# Keto Authorization

## Permission Model

- `STAC Items` are arranged into a hierarchy of `STAC Collections`.
- A `user` can be a member of a `group`.
- A `user` can be the owner, editor, or viewer of a `STAC Collection`.
- A `group` can be the editor or viewer of a `STAC Collection`.
- A `user` can be the owner, editor, or viewer of a `STAC Item`.
- A `group` can be the editor or viewer of a `STAC Item`.

- The owner of a `STAC Item` is also an editor of that `STAC Item`.
- An editor of a `STAC Item` is also a viewer of that `STAC Item`.
- A `user` inherits the permissions of the `group` that they are in.
- `Users` that can view the parent `STAC Collection` in the hierarchy can also view all `STAC Collections` and `STAC Items` the parent `STAC Collection` contains.

### For later...

### Subjects

[Subjects](https://www.ory.sh/docs/keto/concepts/subjects) are the which are the people or things that want to access these resources.

- User
- Group

### Objects

[Objects](https://www.ory.sh/docs/keto/concepts/objects) are the resources that you want to manage, entities in an application.

- STAC Item
- STAC Collection

## Test Model

**Who are viewers/editors/owners of collection `cmip6`?**

```sh
keto expand viewers StacCollection cmip6 --insecure-disable-transport-security
keto expand editors StacCollection cmip6 --insecure-disable-transport-security
keto expand owners StacCollection cmip6 --insecure-disable-transport-security
```

**Can users view collection `cmip6`?**

```sh
keto check alice view StacCollection cmip6 --insecure-disable-transport-security
keto check bob view StacCollection cmip6 --insecure-disable-transport-security
keto check carlos view StacCollection cmip6 --insecure-disable-transport-security
keto check david view StacCollection cmip6 --insecure-disable-transport-security
```
