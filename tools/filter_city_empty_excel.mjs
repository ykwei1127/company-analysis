import fs from "node:fs/promises";
import path from "node:path";
import { FileBlob, SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const workspaceDir = process.cwd();
const inputPath = path.join(workspaceDir, "output", "glassdoor_ratings_20260626_0431.xlsx");
const outputPath = path.join(
  workspaceDir,
  "output",
  "glassdoor_ratings_20260626_0431_without_city_empty.xlsx",
);
const previewPath = path.join(workspaceDir, "output", "glassdoor_ratings_20260626_0431_without_city_empty_preview.png");

function normalizeCell(value) {
  return typeof value === "string" ? value.trim() : value;
}

const input = await FileBlob.load(inputPath);
const sourceWorkbook = await SpreadsheetFile.importXlsx(input);

const workbookSummary = await sourceWorkbook.inspect({
  kind: "sheet,table",
  include: "id,name",
  maxChars: 3000,
  tableMaxRows: 5,
  tableMaxCols: 8,
});
console.log(workbookSummary.ndjson);

let sourceSheet = null;
let sourceValues = null;
let sourceModeColumn = -1;

for (const sheet of sourceWorkbook.worksheets.items) {
  const usedRange = sheet.getUsedRange();
  const values = usedRange?.values ?? [];
  if (!Array.isArray(values) || values.length === 0) {
    continue;
  }

  const headerRow = values[0].map(normalizeCell);
  const columnIndex = headerRow.findIndex(
    (cell) => typeof cell === "string" && cell.toLowerCase() === "source mode",
  );

  if (columnIndex >= 0) {
    sourceSheet = sheet;
    sourceValues = values;
    sourceModeColumn = columnIndex;
    break;
  }
}

if (!sourceSheet || !sourceValues || sourceModeColumn < 0) {
  throw new Error('Could not find a worksheet with a "Source Mode" column.');
}

const headerRow = sourceValues[0];
const dataRows = sourceValues.slice(1);
const filteredRows = dataRows.filter(
  (row) => normalizeCell(row[sourceModeColumn]) !== "city+empty",
);

const removedCount = dataRows.length - filteredRows.length;

const workbook = Workbook.create();
const sheet = workbook.worksheets.add(sourceSheet.name);
sheet.getRangeByIndexes(0, 0, 1 + filteredRows.length, headerRow.length).values = [
  headerRow,
  ...filteredRows,
];

sheet.getRangeByIndexes(0, 0, 1, headerRow.length).format = {
  fill: "#1F4E78",
  font: { bold: true, color: "#FFFFFF" },
};
sheet.getUsedRange().format.autofitColumns();
sheet.getUsedRange().format.autofitRows();
sheet.freezePanes.freezeRows(1);

const verification = await workbook.inspect({
  kind: "table",
  sheetId: sheet.name,
  range: `A1:P6`,
  include: "values",
  tableMaxRows: 6,
  tableMaxCols: 16,
  maxChars: 3000,
});
console.log(verification.ndjson);

const preview = await workbook.render({
  sheetName: sheet.name,
  autoCrop: "all",
  scale: 1,
  format: "png",
});
await fs.writeFile(previewPath, new Uint8Array(await preview.arrayBuffer()));

const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(outputPath);

console.log(
  JSON.stringify({
    inputPath,
    outputPath,
    totalRows: dataRows.length,
    keptRows: filteredRows.length,
    removedRows: removedCount,
  }),
);
