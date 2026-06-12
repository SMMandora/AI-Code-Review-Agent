import { slugify } from "./slug";

test("basic slug", () => {
  expect(slugify("Hello World!")).toBe("hello-world");
});

test("numbers preserved", () => {
  expect(slugify("Item 42")).toBe("item-42");
});
