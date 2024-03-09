import { spice } from "@/spicedb";
import { v1 } from "@authzed/authzed-node";
import { RelationshipList } from "@/components/RelationshipList";

export default async function ResourceType({
  params,
}: {
  params: { resource_type: string };
}) {
  const response = await spice.readRelationships(
    v1.ReadRelationshipsRequest.create({
      relationshipFilter: { resourceType: params.resource_type },
    })
  );
  return (
    <div>
      <h1>
        Resource <span className="font-mono">{params.resource_type}</span>
      </h1>
      <RelationshipList relationships={response} />
    </div>
  );
}
