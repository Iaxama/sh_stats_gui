import { useEffect, useRef, useState } from 'react';
import Cropper from 'react-easy-crop';
import { uploadAvatar, updatePlayer } from '../api';

function getCroppedBlob(imageSrc, crop, zoom) {
  return new Promise((resolve) => {
    const img = new Image();
    img.src = imageSrc;
    img.onload = () => {
      const canvas = document.createElement('canvas');
      const size = 200;
      canvas.width = size;
      canvas.height = size;
      const ctx = canvas.getContext('2d');
      const scaleX = img.naturalWidth / img.width;
      const scaleY = img.naturalHeight / img.height;
      ctx.drawImage(
        img,
        crop.x * scaleX, crop.y * scaleY,
        crop.width * scaleX, crop.height * scaleY,
        0, 0, size, size
      );
      canvas.toBlob(resolve, 'image/jpeg', 0.9);
    };
  });
}

export default function AvatarCrop({ playerId, onDone, onCancel }) {
  const [src, setSrc] = useState(null);
  const [crop, setCrop] = useState({ x: 0, y: 0 });
  const [zoom, setZoom] = useState(1);
  const [croppedArea, setCroppedArea] = useState(null);
  const [saving, setSaving] = useState(false);
  const inputRef = useRef();

  useEffect(() => { inputRef.current?.click(); }, []);

  function handleFile(e) {
    const file = e.target.files[0];
    if (!file) { onCancel(); return; }
    const url = URL.createObjectURL(file);
    setSrc(url);
  }

  async function handleSave() {
    if (!croppedArea) return;
    setSaving(true);
    try {
      const blob = await getCroppedBlob(src, croppedArea, zoom);
      const file = new File([blob], 'avatar.jpg', { type: 'image/jpeg' });
      const result = await uploadAvatar(playerId, file);
      await updatePlayer(playerId, { avatar_crop: { zoom, x: crop.x, y: crop.y } });
      onDone(result.avatar_path);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="modal-backdrop">
      <div className="modal">
        <h2>Set Avatar</h2>
        <input ref={inputRef} type="file" accept="image/*" style={{ display: 'none' }} onChange={handleFile} />
        {!src && (
          <div style={{ marginTop: '1rem', display: 'flex', gap: '0.6rem', justifyContent: 'flex-end' }}>
            <button className="btn-secondary" onClick={onCancel}>Cancel</button>
            <button className="btn-secondary" onClick={() => inputRef.current?.click()}>Choose File</button>
          </div>
        )}
        {src && (
          <>
            <div style={{ position: 'relative', width: '100%', height: 300, marginTop: '1rem', background: '#111' }}>
              <Cropper
                image={src}
                crop={crop}
                zoom={zoom}
                aspect={1}
                cropShape="round"
                onCropChange={setCrop}
                onZoomChange={setZoom}
                onCropComplete={(_, area) => setCroppedArea(area)}
              />
            </div>
            <div className="field" style={{ marginTop: '1rem' }}>
              <label>Zoom</label>
              <input type="range" min={1} max={3} step={0.05} value={zoom}
                onChange={e => setZoom(Number(e.target.value))} />
            </div>
            <div className="modal-actions">
              <button className="btn-secondary" onClick={onCancel}>Cancel</button>
              <button className="btn-primary" onClick={handleSave} disabled={saving}>
                {saving ? 'Saving…' : 'Save Avatar'}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
