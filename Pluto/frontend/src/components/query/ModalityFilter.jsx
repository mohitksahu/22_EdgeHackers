const modalities = [
  { id: 'text', label: 'Text Documents' },
  { id: 'image', label: 'Images' },
  { id: 'audio', label: 'Audio Recordings' },
];

function ModalityFilter({ selected, onChange }) {
  const handleChange = (modalityId) => {
    if (selected.includes(modalityId)) {
      onChange(selected.filter(id => id !== modalityId));
    } else {
      onChange([...selected, modalityId]);
    }
  };

  return (
    <div>
      <label className="block text-sm font-medium text-[var(--text-color,#ffffff)] mb-2">
        Select modalities to search
      </label>
      <div className="flex flex-wrap gap-4">
        {modalities.map((modality) => (
          <label key={modality.id} className="flex items-center text-[var(--text-color,#ffffff)]">
            <input
              type="checkbox"
              checked={selected.includes(modality.id)}
              onChange={() => handleChange(modality.id)}
              className="mr-2"
            />
            {modality.label}
          </label>
        ))}
      </div>
    </div>
  );
}

export default ModalityFilter;
