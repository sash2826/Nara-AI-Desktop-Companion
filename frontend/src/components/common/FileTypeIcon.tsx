import type { ComponentProps } from "react";
import type { IconType } from "react-icons";
import {
  FaFileAlt,
  FaFileArchive,
  FaFileAudio,
  FaFileCode,
  FaFileExcel,
  FaFileImage,
  FaFilePdf,
  FaFilePowerpoint,
  FaFileVideo,
  FaFileWord,
} from "react-icons/fa";
import { cn } from "@/lib/utils";

type IconComponent = IconType;

const FILE_TYPE_ICONS: Record<string, IconComponent> = {
  pdf: FaFilePdf,
  doc: FaFileWord,
  docx: FaFileWord,
  odt: FaFileWord,
  rtf: FaFileWord,
  txt: FaFileAlt,
  md: FaFileAlt,
  xls: FaFileExcel,
  xlsx: FaFileExcel,
  csv: FaFileExcel,
  ods: FaFileExcel,
  ppt: FaFilePowerpoint,
  pptx: FaFilePowerpoint,
  odp: FaFilePowerpoint,
  png: FaFileImage,
  jpg: FaFileImage,
  jpeg: FaFileImage,
  gif: FaFileImage,
  webp: FaFileImage,
  svg: FaFileImage,
  mp3: FaFileAudio,
  wav: FaFileAudio,
  m4a: FaFileAudio,
  flac: FaFileAudio,
  mp4: FaFileVideo,
  mov: FaFileVideo,
  avi: FaFileVideo,
  mkv: FaFileVideo,
  webm: FaFileVideo,
  zip: FaFileArchive,
  rar: FaFileArchive,
  "7z": FaFileArchive,
  tar: FaFileArchive,
  gz: FaFileArchive,
  json: FaFileCode,
  ts: FaFileCode,
  tsx: FaFileCode,
  js: FaFileCode,
  jsx: FaFileCode,
  py: FaFileCode,
  rs: FaFileCode,
  java: FaFileCode,
  cs: FaFileCode,
  go: FaFileCode,
  html: FaFileCode,
  css: FaFileCode,
  xml: FaFileCode,
  yaml: FaFileCode,
  yml: FaFileCode,
  sql: FaFileCode,
};

const FILE_TYPE_COLOURS: Record<string, string> = {
  pdf: "text-destructive",
  doc: "text-primary",
  docx: "text-primary",
  xls: "text-success",
  xlsx: "text-success",
  csv: "text-success",
  ppt: "text-warning",
  pptx: "text-warning",
  png: "text-primary",
  jpg: "text-primary",
  jpeg: "text-primary",
  gif: "text-primary",
  webp: "text-primary",
  mp3: "text-warning",
  wav: "text-warning",
  mp4: "text-destructive",
  mov: "text-destructive",
  zip: "text-warning",
  rar: "text-warning",
  "7z": "text-warning",
  json: "text-primary",
  ts: "text-primary",
  tsx: "text-primary",
  js: "text-warning",
  jsx: "text-warning",
  py: "text-success",
};

export function fileExtension(filePath: string): string {
  const name = filePath.replace(/\\/g, "/").split("/").pop() ?? filePath;
  const dot = name.lastIndexOf(".");
  return dot > 0 ? name.slice(dot + 1).toLowerCase() : "";
}

export function FileTypeIcon({
  path,
  className,
  size = 18,
  ...props
}: ComponentProps<"svg"> & { path: string; size?: number }) {
  const extension = fileExtension(path);
  const Icon = FILE_TYPE_ICONS[extension] ?? FaFileAlt;

  return (
    <Icon
      size={size}
      className={cn(FILE_TYPE_COLOURS[extension] ?? "text-muted-foreground", className)}
      aria-hidden="true"
      {...props}
    />
  );
}
