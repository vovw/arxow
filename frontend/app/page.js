"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  AlertDialog,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogDescription,
} from "@/components/ui/alert-dialog";
import { Loader2 } from "lucide-react";

const ImageDisplay = ({ imageData }) => {
  return (
    <Card className="w-full mb-4">
      <CardContent className="p-4">
        <div className="relative">
          <img
            src={`data:image/png;base64,${imageData.image}`}
            alt={imageData.caption || "Paper figure"}
            className="w-full h-auto object-contain"
          />
          {imageData.caption && (
            <p className="mt-2 text-sm text-gray-600">{imageData.caption}</p>
          )}
          <p className="text-xs text-gray-400">
            Page {imageData.page_number}
            {imageData.reference && ` | Reference: ${imageData.reference}`}
          </p>
        </div>
      </CardContent>
    </Card>
  );
};

export default function Home() {
  const [file, setFile] = useState(null);
  const [documentId, setDocumentId] = useState(null);
  const [analysis, setAnalysis] = useState({
    first_pass: null,
    second_pass: null,
    third_pass: null,
  });
  const [images, setImages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [currentPass, setCurrentPass] = useState(1);
  const [metadata, setMetadata] = useState(null);

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    setFile(file);
    setAnalysis({
      first_pass: null,
      second_pass: null,
      third_pass: null,
    });
    setImages([]);
    setDocumentId(null);
    setCurrentPass(1);
    setMetadata(null);
  };

  const uploadDocument = async () => {
    if (!file) return;

    setLoading(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch("http://localhost:8000/upload/paper", {
        method: "POST",
        body: formData,
      });

      const data = await response.json();
      setDocumentId(data.document_id);
      setMetadata(data.metadata);
      return data.document_id;
    } catch (error) {
      console.error("Error uploading document:", error);
    } finally {
      setLoading(false);
    }
  };

  const analyzePaper = async (passNumber) => {
    if (!documentId && file) {
      const newDocId = await uploadDocument();
      if (!newDocId) return;
    }

    setLoading(true);
    try {
      const response = await fetch(
        `http://localhost:8000/analyze/paper/${documentId}?pass_number=${passNumber}`,
        {
          method: "POST",
        },
      );

      const data = await response.json();

      setAnalysis((prev) => ({
        ...prev,
        [`pass_${passNumber}`]: data.analysis,
      }));

      if (data.images) {
        setImages(data.images);
      }

      setCurrentPass(passNumber);
    } catch (error) {
      console.error("Error analyzing paper:", error);
    } finally {
      setLoading(false);
    }
  };

  const renderAnalysisContent = (content) => {
    try {
      const parsedContent =
        typeof content === "string" ? JSON.parse(content) : content;

      return (
        <div className="space-y-4">
          {Object.entries(parsedContent).map(([key, value]) => (
            <Card key={key} className="w-full">
              <CardHeader>
                <CardTitle className="text-lg">
                  {key.replace(/_/g, " ").toUpperCase()}
                </CardTitle>
              </CardHeader>
              <CardContent>
                {typeof value === "object" ? (
                  Array.isArray(value) ? (
                    <ul className="list-disc pl-6 space-y-2">
                      {value.map((item, index) => (
                        <li key={index} className="text-sm">
                          {item}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <ul className="space-y-2">
                      {Object.entries(value).map(([subKey, subValue]) => (
                        <li key={subKey} className="text-sm">
                          <span className="font-medium">
                            {subKey.replace(/_/g, " ")}:{" "}
                          </span>
                          {typeof subValue === "object"
                            ? JSON.stringify(subValue)
                            : subValue}
                        </li>
                      ))}
                    </ul>
                  )
                ) : (
                  <p className="text-sm">{value}</p>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      );
    } catch (error) {
      console.error("Error rendering content:", error);
      return (
        <Card className="w-full">
          <CardContent>Error rendering analysis</CardContent>
        </Card>
      );
    }
  };

  return (
    <div className="container mx-auto py-8 px-4">
      <h1 className="text-3xl font-bold mb-8 text-center">
        arxow - the arxiv paper diluter
      </h1>

      <Card className="mb-8">
        <CardContent className="pt-6">
          <div className="space-y-6">
            <Input
              type="file"
              accept=".pdf"
              onChange={handleFileUpload}
              className="w-full"
            />

            <div className="flex flex-wrap gap-4 justify-center">
              <Button
                onClick={() => analyzePaper(1)}
                disabled={!file || loading}
                variant={currentPass === 1 ? "default" : "outline"}
              >
                First Pass
              </Button>

              <Button
                onClick={() => analyzePaper(2)}
                disabled={!file || !analysis.pass_1 || loading}
                variant={currentPass === 2 ? "default" : "outline"}
              >
                Second Pass
              </Button>

              <Button
                onClick={() => analyzePaper(3)}
                disabled={!file || !analysis.pass_2 || loading}
                variant={currentPass === 3 ? "default" : "outline"}
              >
                Third Pass
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {loading && (
        <AlertDialog open={loading}>
          <AlertDialogContent className="max-w-md">
            <AlertDialogHeader>
              <AlertDialogTitle className="flex items-center gap-2">
                <Loader2 className="h-5 w-5 animate-spin" />
                {documentId ? "Analyzing Paper" : "Uploading Paper"}
              </AlertDialogTitle>
              <AlertDialogDescription>
                Please wait while we {documentId ? "analyze" : "upload"} your
                paper...
              </AlertDialogDescription>
            </AlertDialogHeader>
          </AlertDialogContent>
        </AlertDialog>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Analysis Content */}
        <div className="space-y-6">
          {metadata && (
            <Card className="w-full">
              <CardHeader>
                <CardTitle>Document Metadata</CardTitle>
              </CardHeader>
              <CardContent>
                <pre className="text-sm">
                  {JSON.stringify(metadata, null, 2)}
                </pre>
              </CardContent>
            </Card>
          )}

          {analysis[`pass_${currentPass}`] && (
            <div>
              <h2 className="text-2xl font-semibold mb-4">
                Pass {currentPass} Analysis
              </h2>
              {renderAnalysisContent(analysis[`pass_${currentPass}`])}
            </div>
          )}
        </div>

        {/* Images Panel */}
        {images.length > 0 && (
          <div className="space-y-6">
            <h2 className="text-2xl font-semibold mb-4">Paper Figures</h2>
            <div className="space-y-4">
              {images.map((imageData, index) => (
                <ImageDisplay key={index} imageData={imageData} />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
