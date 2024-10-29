import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ReactNode } from "react";

export interface MessageCardProps {
  role: string;
  sanitizedHtml?: string;
  content?: ReactNode;
}
export const MessageCard = ({ role, content }: MessageCardProps) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{role}</CardTitle>
      </CardHeader>
      <CardContent className='flex flex-col gap-2'>{content}</CardContent>
    </Card>
  );
};
