import { Badge } from "@/components/ui/badge";
import { Combobox } from "@/components/ui/combobox";
import { TagPublic } from "@/types/types";
import { spanQueryOptions, useUpdateSpanMutation } from "@/utils/spans";
import { tagsByProjectsQueryOptions, useCreateTagMutation } from "@/utils/tags";
import { useSuspenseQuery } from "@tanstack/react-query";
import { Plus } from "lucide-react";
import { useEffect, useRef, useState } from "react";

export const TagPopover = ({
  spanUuid,
  projectUuid,
}: {
  spanUuid: string;
  projectUuid: string;
}) => {
  const { data: span } = useSuspenseQuery(spanQueryOptions(spanUuid));
  const { data: availableTags } = useSuspenseQuery(
    tagsByProjectsQueryOptions(projectUuid)
  );
  const createTag = useCreateTagMutation();
  const updateSpan = useUpdateSpanMutation();

  // Maintain popover state
  const [isOpen, setIsOpen] = useState(false);

  // Use refs to track previous state and avoid unnecessary re-renders
  const prevTagsRef = useRef<TagPublic[]>([]);

  // Use state for selected tags but initialize only once
  const [selectedTags, setSelectedTags] = useState<TagPublic[]>(
    () => span.tags ?? []
  );

  // Only update selected tags if span tags change from external source
  useEffect(() => {
    const spanTags = span.tags ?? [];
    // Deep comparison to avoid unnecessary state updates
    if (JSON.stringify(prevTagsRef.current) !== JSON.stringify(spanTags)) {
      setSelectedTags(spanTags);
      prevTagsRef.current = spanTags;
    }
  }, [span.tags]);

  const tagMapping = availableTags.reduce(
    (acc, tag) => {
      acc[tag.uuid] = tag;
      return acc;
    },
    {} as Record<string, TagPublic>
  );

  // Convert from TagPublic[] to string[] for Combobox value
  const selectedTagIds = selectedTags.map((tag) => tag.uuid);

  const handleTagChange = async (tagUuids: string[]) => {
    // Find the full TagPublic objects for the selected UUIDs
    const tagObjects: TagPublic[] = tagUuids
      .map((uuid) => tagMapping[uuid])
      .filter(Boolean); // Filter out any undefined values

    // Use optimistic updates to avoid UI flicker
    const previousTags = [...selectedTags];

    // Update local state immediately for better UX
    setSelectedTags(tagObjects);

    try {
      // Update server state
      await updateSpan.mutateAsync({
        spanUuid,
        spanUpdate: {
          tags_by_uuid: tagObjects.map((tag) => tag.uuid),
        },
      });

      // Update ref after successful mutation
      prevTagsRef.current = tagObjects;
    } catch (error) {
      // Revert to previous state on error
      setSelectedTags(previousTags);
      console.error("Failed to update tags:", error);
    }
  };

  const handleAddNewTag = async (tagName: string) => {
    if (!tagName.trim()) return;

    try {
      // Keep popover open during tag creation
      setIsOpen(true);

      // Create the new tag
      const newTag = await createTag.mutateAsync({
        name: tagName.trim(),
        project_uuid: projectUuid,
      });

      if (newTag) {
        const updatedTags = [...selectedTags, newTag];

        setSelectedTags(updatedTags);

        await updateSpan.mutateAsync({
          spanUuid,
          spanUpdate: {
            tags_by_uuid: updatedTags.map((tag) => tag.uuid),
          },
        });
      }
    } catch (error) {
      console.error("Failed to create tag:", error);
    }
  };

  return (
    <Combobox
      multiple={true}
      customTrigger={
        <Badge pill variant="outline" size="lg">
          <Plus />
        </Badge>
      }
      items={availableTags.map((tag) => ({
        value: tag.uuid,
        label: tag.name,
      }))}
      value={selectedTagIds}
      withEmoji={true}
      onChange={handleTagChange}
      onAddItem={handleAddNewTag}
      disableAdd={false}
      popoverText="Add tags..."
      helperText="Search or create tags..."
      emptyText="No matching tags found. Type to create a new one."
      open={isOpen}
      onOpenChange={setIsOpen}
    />
  );
};
