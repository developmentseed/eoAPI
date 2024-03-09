"use client";
import { v1 } from "@authzed/authzed-node";
import { Pill } from "@/components/Pill";
import { useState } from "react";
import Link from "next/link";

type ResourceType = "subject" | "relation" | "resource";

export const RelationshipList: React.FC<{
  relationships: v1.ReadRelationshipsResponse[];
}> = ({ relationships }) => {
  const [selected, setSelected] = useState<
    [ResourceType, string] | undefined
  >();
  return (
    <ul>
      {relationships.map(({ relationship }, i) => {
        const subject = `${relationship!.subject!.object!.objectType}:${
          relationship!.subject!.object!.objectId
        }`;
        const relation = relationship!.relation;
        const resource = `${relationship!.resource!.objectType}:${
          relationship!.resource!.objectId
        }`;

        return (
          <li key={i} className="my-4">
            <Relationship
              {...{ subject, relation, resource, selected, setSelected }}
            />
          </li>
        );
      })}
    </ul>
  );
};

export const Relationship: React.FC<{
  subject: string;
  relation: string;
  resource: string;
  selected?: [ResourceType, string];
  setSelected: (type_id?: [ResourceType, string]) => void;
}> = ({ selected, setSelected, ...props }) => {
  const match = selected ? props[selected[0]] === selected[1] : true;
  const { subject, relation, resource } = props;
  return (
    <>
      <Link href={`/resource/${subject.split(":").join("/")}`}>
        <Pill
          color={match ? "blue" : "gray"}
          onMouseEnter={(e) => setSelected(["subject", subject])}
          onMouseLeave={() => setSelected()}
        >
          {subject}
        </Pill>
      </Link>
      is
      <Pill
        color={match ? "green" : "gray"}
        onMouseEnter={(e) => setSelected(["relation", relation])}
        onMouseLeave={() => setSelected()}
      >
        {relation}
      </Pill>
      of
      <Link href={`/resource/${resource.split(":").join("/")}`}>
        <Pill
          color={match ? "purple" : "gray"}
          onMouseEnter={(e) => setSelected(["resource", resource])}
          onMouseLeave={() => setSelected()}
        >
          {resource}
        </Pill>
      </Link>
    </>
  );
};
