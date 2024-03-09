import { v1 } from "@authzed/authzed-node";
import { ClientSecurity } from "@authzed/authzed-node/dist/src/util";

const token = process.env.SPICEDB_TOKEN;

export const { promises: spice } = v1.NewClient(
  token!,
  "spicedb:50051",
  ClientSecurity.INSECURE_PLAINTEXT_CREDENTIALS
);

const buildObjectReference = (objectType: string) => (objectId: string) =>
  v1.ObjectReference.create({ objectType, objectId });

export const collection = buildObjectReference("collection");

export const user = buildObjectReference("user");

export const subject = (object: v1.ObjectReference) =>
  v1.SubjectReference.create({ object });

export const hasPermission = (
  resource: v1.ObjectReference,
  permission: string,
  subject: v1.SubjectReference
) => v1.CheckPermissionRequest.create({ resource, permission, subject });

const checkPermissionRequest = v1.CheckPermissionRequest.create({
  resource: collection("public"),
  permission: "read",
  subject: subject(user("xyz")),
});
