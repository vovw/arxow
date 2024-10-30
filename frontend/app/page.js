"use client";

import { useState } from "react";
import styles from "./page.module.css";

export default function Home() {
  const [file, setFile] = useState(null);
  const [analysis, setAnalysis] = useState({
    first_pass: null,
    second_pass: null,
    third_pass: null,
  });
  const [loading, setLoading] = useState(false);
  const [currentPass, setCurrentPass] = useState(1); // Add state for current pass

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    setFile(file);
    setAnalysis({
      first_pass: null,
      second_pass: null,
      third_pass: null,
    });
    setCurrentPass(1); // Reset to first pass when new file is uploaded
  };

  const analyzePaper = async (passNumber) => {
    if (!file) return;

    setLoading(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      console.log("Analyzing paper for pass:", passNumber); // Debug statement
      const response = await fetch(
        `http://localhost:8000/analyze/paper?pass_number=${passNumber}`,
        {
          method: "POST",
          body: formData,
        },
      );

      const data = await response.json();
      console.log("Received analysis data:", data); // Debug statement

      setAnalysis((prev) => {
        const newAnalysis = {
          ...prev,
          [`first_pass`]: passNumber === 1 ? data.analysis : prev.first_pass,
          [`second_pass`]: passNumber === 2 ? data.analysis : prev.second_pass,
          [`third_pass`]: passNumber === 3 ? data.analysis : prev.third_pass,
        };
        console.log("Updated analysis state:", newAnalysis); // Debug statement
        return newAnalysis;
      });
      setCurrentPass(passNumber);
    } catch (error) {
      console.error("Error analyzing paper:", error);
    } finally {
      setLoading(false);
    }
  };

  const renderAnalysisContent = (content) => {
    console.log("Rendering content:", content); // Debug statement

    try {
      const parsedContent =
        typeof content === "string" ? JSON.parse(content) : content;
      console.log("Parsed content:", parsedContent); // Debug statement

      return (
        <div className={styles.analysisContent}>
          {Object.entries(parsedContent).map(([key, value]) => {
            console.log("Rendering section:", key, value); // Debug statement
            return (
              <div key={key} className={styles.analysisSection}>
                <h3>{key.replace(/_/g, " ").toUpperCase()}</h3>
                {typeof value === "object" ? (
                  Array.isArray(value) ? (
                    <ul>
                      {value.map((item, index) => (
                        <li key={index}>{item}</li>
                      ))}
                    </ul>
                  ) : (
                    <ul>
                      {Object.entries(value).map(([subKey, subValue]) => (
                        <li key={subKey}>
                          <strong>{subKey.replace(/_/g, " ")}:</strong>{" "}
                          {typeof subValue === "object"
                            ? JSON.stringify(subValue)
                            : subValue}
                        </li>
                      ))}
                    </ul>
                  )
                ) : (
                  <p>{value}</p>
                )}
              </div>
            );
          })}
        </div>
      );
    } catch (error) {
      console.error("Error rendering content:", error); // Debug statement
      return (
        <div className={styles.analysisContent}>Error rendering analysis</div>
      );
    }
  };

  return (
    <div className={styles.container}>
      <h1>Research Paper Analyzer</h1>

      <div className={styles.uploadSection}>
        <input type="file" accept=".pdf" onChange={handleFileUpload} />

        <div className={styles.passButtons}>
          <button
            onClick={() => {
              if (analysis.first_pass) {
                setCurrentPass(1);
              } else {
                analyzePaper(1);
              }
            }}
            disabled={!file || loading}
            className={currentPass === 1 ? styles.activeButton : ""}
          >
            First Pass
          </button>

          <button
            onClick={() => {
              if (analysis.second_pass) {
                setCurrentPass(2);
              } else {
                analyzePaper(2);
              }
            }}
            disabled={!file || !analysis.first_pass || loading}
            className={currentPass === 2 ? styles.activeButton : ""}
          >
            Second Pass
          </button>

          <button
            onClick={() => {
              if (analysis.third_pass) {
                setCurrentPass(3);
              } else {
                analyzePaper(3);
              }
            }}
            disabled={!file || !analysis.second_pass || loading}
            className={currentPass === 3 ? styles.activeButton : ""}
          >
            Third Pass
          </button>
        </div>
      </div>

      {loading && <div className={styles.loading}>Analyzing paper...</div>}

      <div className={styles.results}>
        {analysis.first_pass && currentPass === 1 && (
          <div className={styles.passResult}>
            <h2>First Pass Analysis</h2>
            {renderAnalysisContent(analysis.first_pass)}
          </div>
        )}

        {analysis.second_pass && currentPass === 2 && (
          <div className={styles.passResult}>
            <h2>Second Pass Analysis</h2>
            {renderAnalysisContent(analysis.second_pass)}
          </div>
        )}

        {analysis.third_pass && currentPass === 3 && (
          <div className={styles.passResult}>
            <h2>Third Pass Analysis</h2>
            {renderAnalysisContent(analysis.third_pass)}
          </div>
        )}
      </div>
    </div>
  );
}
