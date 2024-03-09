import { spice } from "@/spicedb";
import { v1 } from "@authzed/authzed-node";
import { RelationshipList } from "@/components/RelationshipList";

export default async function Home() {
  const response = await spice.readRelationships(
    v1.ReadRelationshipsRequest.create({
      relationshipFilter: { resourceType: "collection" },
    })
  );
  return <RelationshipList relationships={response} />;
}
