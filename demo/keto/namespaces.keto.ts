import { Namespace, SubjectSet, Context } from "@ory/keto-namespace-types";

// https://www.ory.sh/docs/keto/modeling/create-permission-model
class User implements Namespace {}

// class Group implements Namespace {
//   related: {
//     members: User[];
//   };
// }

class StacItem implements Namespace {
  related: {
    owners: User[];
    editors: User[];
    viewers: User[];
    parents: StacCollection[];
  };

  permits = {
    view: (ctx: Context): boolean =>
      this.related.viewers.includes(ctx.subject) ||
      this.related.editors.includes(ctx.subject) ||
      this.related.owners.includes(ctx.subject) ||
      this.related.parents.traverse((parent) => parent.permits.view(ctx)),
    edit: (ctx: Context): boolean =>
      this.related.editors.includes(ctx.subject) ||
      this.related.owners.includes(ctx.subject) ||
      this.related.parents.traverse((parent) => parent.permits.edit(ctx)),
    delete: (ctx: Context): boolean =>
      this.related.owners.includes(ctx.subject),
  };
}

class StacCollection implements Namespace {
  related: {
    owners: User[];
    editors: User[];
    viewers: User[];
    parents: StacCollection[];
  };

  permits = {
    view: (ctx: Context): boolean =>
      this.related.viewers.includes(ctx.subject) ||
      this.related.editors.includes(ctx.subject) ||
      this.related.owners.includes(ctx.subject) ||
      this.related.parents.traverse((parent) => parent.permits.view(ctx)),
    edit: (ctx: Context): boolean =>
      this.related.editors.includes(ctx.subject) ||
      this.related.owners.includes(ctx.subject) ||
      this.related.parents.traverse((parent) => parent.permits.edit(ctx)),
    delete: (ctx: Context): boolean =>
      this.related.owners.includes(ctx.subject),
  };
}
