import { useQuery } from "@tanstack/react-query";

import type { components } from "@/api/schema";
import { ColumnHeader } from "@/components/ColumnHeader";
import { PageHeader } from "@/components/PageHeader";
import { SectionHeader } from "@/components/SectionHeader";
import { Card } from "@/components/ui/card";
import { copy } from "@/copy/pl";
import { api } from "@/lib/api";

type AboutData = components["schemas"]["AboutPage"];
type TeamGroup = components["schemas"]["TeamGroup"];
type TeamMember = components["schemas"]["TeamMember"];

async function fetchAbout(): Promise<AboutData> {
  const { data, response } = await api.GET("/api/about/");
  if (data === undefined) {
    throw new Error(`The About request failed with ${String(response.status)}.`);
  }
  return data;
}

function hasText(text: string): boolean {
  return text.trim() !== "";
}

/** Plain text until step 10 makes it rich text: blank lines separate paragraphs. */
function paragraphs(text: string): string[] {
  return text
    .split(/\n\s*\n/)
    .map((paragraph) => paragraph.trim())
    .filter(Boolean);
}

/** "Osoba" in design/components/. An empty role or biography is not rendered (R-02). */
function Person({ member }: { member: TeamMember }) {
  return (
    <li className="flex flex-col gap-4 border-b border-border py-12">
      <p className="text-lora-tytul-elementu text-foreground">{member.name}</p>
      {hasText(member.role) && (
        <p className="text-cousine-metadane-male text-accent-foreground">{member.role}</p>
      )}
      {hasText(member.bio) && (
        <p className="text-lora-tekst-maly text-muted-foreground">{member.bio}</p>
      )}
    </li>
  );
}

function Team({ groups }: { groups: TeamGroup[] }) {
  return (
    <Card>
      <SectionHeader title={copy.about.team} />
      {/* The API leaves out empty groups and returns the rest in the story's order. */}
      {groups.map(({ group, members }) => (
        <div key={group} className="flex flex-col gap-8">
          <ColumnHeader label={copy.about.groups[group]} />
          <ul>
            {members.map((member, index) => (
              <Person key={index} member={member} />
            ))}
          </ul>
        </div>
      ))}
    </Card>
  );
}

/** The About page (US-RA-13). Blocks without content are not rendered (R-02). */
export function AboutPage() {
  const about = useQuery({ queryKey: ["about"], queryFn: fetchAbout });
  const intro = about.data?.intro ?? "";
  const project = paragraphs(about.data?.project ?? "");
  const team = about.data?.team ?? [];

  return (
    <main className="flex flex-col">
      <PageHeader
        label={copy.siteName}
        title={copy.about.title}
        description={hasText(intro) ? intro : undefined}
      />
      <div className="px-page-mobile py-24 md:px-page md:pt-48 md:pb-64">
        <div className="mx-auto flex w-full max-w-3xl flex-col gap-32">
          {(about.isPending || about.isError) && (
            <p className="text-cousine-metadane text-muted-foreground" role="status">
              {about.isPending ? copy.about.loading : copy.about.error}
            </p>
          )}
          {project.length > 0 && (
            <Card>
              <SectionHeader title={copy.about.project} />
              <div className="flex flex-col gap-16">
                {project.map((paragraph, index) => (
                  <p key={index} className="text-lora-tekst text-foreground">
                    {paragraph}
                  </p>
                ))}
              </div>
            </Card>
          )}
          {team.length > 0 && <Team groups={team} />}
        </div>
      </div>
    </main>
  );
}
