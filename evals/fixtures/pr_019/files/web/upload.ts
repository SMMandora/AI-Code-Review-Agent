import * as fs from "fs";
import * as path from "path";

export async function handleUpload(
  filename: string,
  data: Buffer
): Promise<string> {
  const dest = path.join("/uploads", filename);
  await fs.promises.writeFile(dest, data);
  return dest;
}
