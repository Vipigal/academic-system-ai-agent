import { isRecord } from "./guards";

export enum Modality {
  OnCampus = "Presencial",
  Distance = "EAD",
}

export interface DevStudent {
  brand: string;
  studentId: string;
  fullName: string;
  status: string;
}

export interface Offering {
  brand: string;
  modality: Modality;
  students: DevStudent[];
}

export interface Institution {
  name: string;
  offerings: Offering[];
}

const DISTANCE_SUFFIX = "_EAD";
const LOWERCASE_PARTICLES = new Set(["da", "das", "de", "do", "dos", "e"]);
const STATUS_LABELS: Record<string, string> = {
  ACTIVE: "Ativo",
  LOCKED: "Trancado",
  DROPOUT: "Evadido",
  TRANSFERRED: "Transferido",
  GRADUATED: "Formado",
  CANCELLED: "Cancelado",
};

function parseStudent(row: unknown): DevStudent | null {
  if (!isRecord(row)) return null;
  const { brand, student_id: studentId, full_name: fullName, status } = row;
  if (typeof brand !== "string" || typeof studentId !== "string") return null;
  if (typeof fullName !== "string" || typeof status !== "string") return null;
  return { brand, studentId, fullName, status };
}

export function parseStudents(payload: unknown): DevStudent[] {
  if (!Array.isArray(payload)) return [];
  return payload.map(parseStudent).filter((student) => student !== null);
}

export function institutionName(brand: string): string {
  return brand.replace(DISTANCE_SUFFIX, "");
}

function offeringOf(brand: string, students: DevStudent[]): Offering {
  const distance = brand.endsWith(DISTANCE_SUFFIX);
  return { brand, modality: distance ? Modality.Distance : Modality.OnCampus, students };
}

function modalityRank(offering: Offering): number {
  return offering.modality === Modality.OnCampus ? 0 : 1;
}

export function groupByInstitution(students: DevStudent[]): Institution[] {
  const byBrand = new Map<string, DevStudent[]>();
  for (const student of students) byBrand.set(student.brand, [...(byBrand.get(student.brand) ?? []), student]);
  const byName = new Map<string, Offering[]>();
  for (const [brand, members] of byBrand) {
    const name = institutionName(brand);
    byName.set(name, [...(byName.get(name) ?? []), offeringOf(brand, members)]);
  }
  return [...byName]
    .map(([name, offerings]) => ({
      name,
      offerings: offerings.sort((left, right) => modalityRank(left) - modalityRank(right)),
    }))
    .sort((left, right) => left.name.localeCompare(right.name));
}

export function displayName(fullName: string): string {
  return fullName
    .toLowerCase()
    .split(/\s+/)
    .map((word) => (LOWERCASE_PARTICLES.has(word) ? word : word.charAt(0).toUpperCase() + word.slice(1)))
    .join(" ");
}

export function firstName(fullName: string): string {
  return displayName(fullName).split(" ")[0] ?? "";
}

export function statusLabel(status: string): string {
  return STATUS_LABELS[status] ?? status;
}

export function loginReference(student: DevStudent): string {
  return `${student.brand}:${student.studentId}`;
}

export function matches(student: DevStudent, query: string): boolean {
  const needle = query.trim().toLowerCase();
  return !needle || student.fullName.toLowerCase().includes(needle) || student.studentId.includes(needle);
}
