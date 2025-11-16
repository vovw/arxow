"use client";

import { useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
import Home from "../../page";

export default function ArxivPdfPaper() {
  const params = useParams();
  const router = useRouter();
  const paperId = params.id?.replace('.pdf', '');

  useEffect(() => {
    if (paperId) {
      router.push(`/?arxiv=${paperId}`);
    }
  }, [paperId, router]);

  return <Home />;
}
