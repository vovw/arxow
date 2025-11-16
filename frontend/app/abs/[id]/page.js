"use client";

import { useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
import Home from "../page";

export default function ArxivPaper() {
  const params = useParams();
  const router = useRouter();
  const paperId = params.id;

  useEffect(() => {
    if (paperId) {
      // Redirect to home with the paper ID in state
      // The home page will handle fetching it
      router.push(`/?arxiv=${paperId}`);
    }
  }, [paperId, router]);

  return <Home />;
}
