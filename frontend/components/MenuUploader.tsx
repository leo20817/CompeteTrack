"use client";

import { useState, useRef } from "react";

interface MenuUploaderProps {
  brandId: string;
  onParsed: (result: any) => void;
}

export default function MenuUploader({ brandId, onParsed }: MenuUploaderProps) {
  const [files, setFiles] = useState<File[]>([]);
  const [previews, setPreviews] = useState<string[]>([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  function handleFiles(newFiles: FileList | null) {
    if (!newFiles) return;
    const arr = Array.from(newFiles).slice(0, 10 - files.length);
    const valid = arr.filter((f) =>
      ["image/jpeg", "image/png", "image/webp"].includes(f.type)
    );

    if (valid.length < arr.length) {
      setError("部分檔案格式不支援，僅接受 JPG、PNG、WebP");
    }

    setFiles((prev) => [...prev, ...valid]);
    valid.forEach((f) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        setPreviews((prev) => [...prev, e.target?.result as string]);
      };
      reader.readAsDataURL(f);
    });
  }

  function removeFile(index: number) {
    setFiles((prev) => prev.filter((_, i) => i !== index));
    setPreviews((prev) => prev.filter((_, i) => i !== index));
  }

  async function handleUpload() {
    if (files.length === 0) return;
    setUploading(true);
    setError("");

    try {
      const formData = new FormData();
      files.forEach((f) => formData.append("files", f));

      const resp = await fetch(`/api/menu-upload/${brandId}/upload`, {
        method: "POST",
        body: formData,
      });
      const json = await resp.json();

      if (json.success) {
        onParsed(json.data);
      } else {
        setError(json.error || "上傳失敗");
      }
    } catch (err) {
      setError("上傳失敗，請重試");
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h4 className="font-semibold mb-3">上傳菜單照片</h4>
      <p className="text-sm text-gray-500 mb-4">
        支援 JPG、PNG、WebP，最多 10 張。AI 會自動辨識品項和價格。
      </p>

      {error && <p className="text-red-500 text-sm mb-3">{error}</p>}

      {/* Drop zone */}
      <div
        className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center cursor-pointer hover:border-blue-400 transition-colors"
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => { e.preventDefault(); e.currentTarget.classList.add("border-blue-400"); }}
        onDragLeave={(e) => { e.currentTarget.classList.remove("border-blue-400"); }}
        onDrop={(e) => { e.preventDefault(); e.currentTarget.classList.remove("border-blue-400"); handleFiles(e.dataTransfer.files); }}
      >
        <input
          ref={inputRef}
          type="file"
          accept="image/jpeg,image/png,image/webp"
          multiple
          className="hidden"
          onChange={(e) => handleFiles(e.target.files)}
        />
        <p className="text-gray-500">
          {files.length === 0
            ? "點擊或拖拽菜單照片到這裡"
            : `已選擇 ${files.length} 張照片`}
        </p>
      </div>

      {/* Previews */}
      {previews.length > 0 && (
        <div className="grid grid-cols-5 gap-2 mt-4">
          {previews.map((src, i) => (
            <div key={i} className="relative group">
              <img src={src} alt={`菜單 ${i + 1}`} className="w-full h-24 object-cover rounded" />
              <button
                onClick={() => removeFile(i)}
                className="absolute top-1 right-1 bg-red-500 text-white rounded-full w-5 h-5 text-xs opacity-0 group-hover:opacity-100 transition-opacity"
              >
                x
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Upload button */}
      {files.length > 0 && (
        <button
          onClick={handleUpload}
          disabled={uploading}
          className="mt-4 w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center gap-2"
        >
          {uploading && <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />}
          {uploading ? "AI 解析中..." : `上傳並解析 (${files.length} 張)`}
        </button>
      )}
    </div>
  );
}
