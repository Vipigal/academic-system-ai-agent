const TIME_ZONE = "America/Sao_Paulo";
const LOWERCASE_WORDS = new Set(["a", "and", "da", "das", "de", "do", "dos", "e", "for", "in", "of", "the", "to"]);
const MS_PER_DAY = 86_400_000;
const ROMAN_NUMERAL = /^(i{1,3}|iv|vi{0,3}|ix|x)$/;

const money = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
const dayMonth = new Intl.DateTimeFormat("pt-BR", { timeZone: TIME_ZONE, day: "2-digit", month: "2-digit" });
const dayKeyFormat = new Intl.DateTimeFormat("en-CA", { timeZone: TIME_ZONE, year: "numeric", month: "2-digit", day: "2-digit" });

export function formatMoney(value: number): string {
  return money.format(value);
}

export function formatPercent(value: number): string {
  return `${value.toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%`;
}

export function formatRate(fraction: number): string {
  return formatPercent(Math.round(fraction * 1000) / 10);
}

export function formatCompetence(competence: string): string {
  const [year, month] = competence.split("-");
  return year && month ? `${month}/${year}` : competence;
}

export function formatHours(value: number): string {
  return `${value.toLocaleString("pt-BR")} h`;
}

function dateOnly(isoDate: string): Date {
  return new Date(`${isoDate}T12:00:00-03:00`);
}

export function formatDayMonth(isoDate: string): string {
  return dayMonth.format(dateOnly(isoDate));
}

export function dayKey(moment: Date): string {
  return dayKeyFormat.format(moment);
}

export function daysBetween(fromIsoDate: string, toIsoDate: string): number {
  return Math.round((dateOnly(toIsoDate).getTime() - dateOnly(fromIsoDate).getTime()) / MS_PER_DAY);
}

export function titleCase(value: string): string {
  return value
    .toLowerCase()
    .split(/\s+/)
    .map((word, index) => {
      if (ROMAN_NUMERAL.test(word)) return word.toUpperCase();
      if (index > 0 && LOWERCASE_WORDS.has(word)) return word;
      return word.charAt(0).toUpperCase() + word.slice(1);
    })
    .join(" ");
}
