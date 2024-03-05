import { Namespace, SubjectSet, Context } from "@ory/keto-namespace-types";

// https://www.ory.sh/docs/keto/modeling/create-permission-model
class User implements Namespace {}

class Group implements Namespace {
  related: {
    members: (User | Group)[];
  };
}

class StacCollection implements Namespace {
  related: {
    parents: StacCollection[];
    viewers: SubjectSet<Group, "members">[];
  };

  permits = {
    view: (ctx: Context): boolean =>
      this.related.viewers.includes(ctx.subject) ||
      this.related.parents.traverse((p) => p.permits.view(ctx)),
  };
}

class StacItem implements Namespace {
  related: {
    parents: StacCollection[];
    viewers: (User | SubjectSet<Group, "members">)[];
    owners: (User | SubjectSet<Group, "members">)[];
  };

  // Some comment
  permits = {
    view: (ctx: Context): boolean =>
      this.related.parents.traverse((p) => p.permits.view(ctx)) ||
      this.related.viewers.includes(ctx.subject) ||
      this.related.owners.includes(ctx.subject),

    edit: (ctx: Context) => this.related.owners.includes(ctx.subject),
  };
}
