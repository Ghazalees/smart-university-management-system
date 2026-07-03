/** Verifies the ui frontend behavior and regression scenarios. */

import { useState } from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { Badge, EmptyState, Input, KpiCard, Modal, ProgressRing, StatusBadge } from "./ui";

describe("professional UI primitives", () => {
  it("maps workflow states to semantic status badges", () => {
    render(<StatusBadge status="under_review" />);
    const badge = screen.getByText("under review");
    expect(badge).toHaveClass("badge-info");
  });

  it("clamps progress values and exposes an accessible label", () => {
    render(<ProgressRing value={140} label="Degree progress" />);
    expect(screen.getByRole("img", { name: "Degree progress: 100%" })).toBeInTheDocument();
    expect(screen.getByText("100%")).toBeInTheDocument();
  });

  it("renders an actionable empty state", () => {
    render(<EmptyState title="No requests" message="Create your first request" action={<button>Start</button>} />);
    expect(screen.getByText("No requests")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Start" })).toBeInTheDocument();
  });

  it("renders KPI semantics and reusable badges", () => {
    render(<><KpiCard label="Open cases" value={12} icon={<span>!</span>} delta={8} /><Badge tone="success">Healthy</Badge></>);
    expect(screen.getByText("Open cases")).toBeInTheDocument();
    expect(screen.getByText("8%")).toHaveClass("delta-up");
    expect(screen.getByText("Healthy")).toHaveClass("badge-success");
  });

  it("keeps focus in a controlled modal field while the parent rerenders", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    function ControlledModal() {
      const [value, setValue] = useState("");
      return <Modal title="Edit request" onClose={onClose}><Input label="Title" value={value} onChange={(event) => setValue(event.target.value)} /></Modal>;
    }

    render(<ControlledModal />);
    const input = screen.getByRole("textbox", { name: "Title" });
    expect(input).toHaveFocus();
    await user.type(input, "Master certificate");
    expect(input).toHaveValue("Master certificate");
    expect(input).toHaveFocus();
    expect(onClose).not.toHaveBeenCalled();
  });

  it("closes a modal with Escape", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    render(<Modal title="Details" onClose={onClose}><button>Action</button></Modal>);
    await user.keyboard("{Escape}");
    expect(onClose).toHaveBeenCalledTimes(1);
  });


  it("closes a modal from its close button", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    render(<Modal title="Document details" onClose={onClose}><button>Action</button></Modal>);
    await user.click(screen.getByRole("button", { name: "Close Document details" }));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("closes only when the backdrop itself is clicked", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    const { container } = render(<Modal title="Workflow details" onClose={onClose}><button>Inside</button></Modal>);
    await user.click(screen.getByRole("button", { name: "Inside" }));
    expect(onClose).not.toHaveBeenCalled();
    const backdrop = container.querySelector(".modal-backdrop");
    expect(backdrop).not.toBeNull();
    await user.click(backdrop as HTMLElement);
    expect(onClose).toHaveBeenCalledTimes(1);
  });
});
