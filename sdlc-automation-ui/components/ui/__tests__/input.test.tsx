import * as React from "react";
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { Input } from "../input";

describe("Input", () => {
  it("renders with placeholder", () => {
    render(<Input placeholder="Enter text..." />);

    expect(screen.getByPlaceholderText("Enter text...")).toBeInTheDocument();
  });

  it("accepts user input", async () => {
    const user = userEvent.setup();
    render(<Input placeholder="Enter text..." />);

    const input = screen.getByRole("textbox");
    await user.type(input, "Hello world");

    expect(input).toHaveValue("Hello world");
  });

  it("applies error styling when error prop is true", () => {
    render(<Input error placeholder="Enter text..." />);

    const input = screen.getByRole("textbox");
    expect(input).toHaveClass("border-error");
  });

  it("forwards ref correctly", () => {
    const ref = React.createRef<HTMLInputElement>();

    render(<Input ref={ref} />);

    expect(ref.current).toBeInstanceOf(HTMLInputElement);
  });
});
