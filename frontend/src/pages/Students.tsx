import React, { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";
import { 
  Search, 
  Download, 
  Upload, 
  Edit2, 
  Trash2, 
  Plus, 
  QrCode, 
  X, 
  FileSpreadsheet,
  ChevronLeft,
  ChevronRight
} from "lucide-react";

export const Students: React.FC = () => {
  const { apiFetch, user } = useAuth();
  const { addToast } = useToast();

  const [students, setStudents] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [limit] = useState(10);
  const [search, setSearch] = useState("");
  const [classFilter, setClassFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isImportOpen, setIsImportOpen] = useState(false);
  const [importFile, setImportFile] = useState<File | null>(null);
  
  // Selected student for details, editing or QR
  const [selectedStudent, setSelectedStudent] = useState<any | null>(null);
  const [isQrOpen, setIsQrOpen] = useState(false);

  // Form Fields
  const [formMode, setFormMode] = useState<"create" | "edit">("create");
  const [formAdmissionNumber, setFormAdmissionNumber] = useState("");
  const [formRollNumber, setFormRollNumber] = useState("");
  const [formName, setFormName] = useState("");
  const [formClass, setFormClass] = useState("");
  const [formSection, setFormSection] = useState("");
  const [formGender, setFormGender] = useState("Male");
  const [formDob, setFormDob] = useState("");
  const [formAddress, setFormAddress] = useState("");
  const [formRfid, setFormRfid] = useState("");
  const [formStatus, setFormStatus] = useState("active");
  
  const [formFatherName, setFormFatherName] = useState("");
  const [formFatherMobile, setFormFatherMobile] = useState("");
  const [formMotherName, setFormMotherName] = useState("");
  const [formMotherMobile, setFormMotherMobile] = useState("");

  const fetchStudents = async () => {
    setLoading(true);
    try {
      const url = `/api/students/?page=${page}&limit=${limit}&query=${search}&class_name=${classFilter}&status=${statusFilter}`;
      const data = await apiFetch(url);
      setStudents(data.students || []);
      setTotal(data.total || 0);
    } catch (e: any) {
      setStudents([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStudents();
  }, [page, classFilter, statusFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchStudents();
  };

  // Open Create Form
  const openCreateModal = () => {
    setFormMode("create");
    setFormAdmissionNumber("");
    setFormRollNumber("");
    setFormName("");
    setFormClass("");
    setFormSection("");
    setFormGender("Male");
    setFormDob("");
    setFormAddress("");
    setFormRfid("");
    setFormStatus("active");
    setFormFatherName("");
    setFormFatherMobile("");
    setFormMotherName("");
    setFormMotherMobile("");
    setIsModalOpen(true);
  };

  // Open Edit Form
  const openEditModal = (student: any) => {
    setFormMode("edit");
    setSelectedStudent(student);
    setFormAdmissionNumber(student.admission_number);
    setFormRollNumber(student.roll_number || "");
    setFormName(student.name);
    setFormClass(student.class_name);
    setFormSection(student.section);
    setFormGender(student.gender || "Male");
    setFormDob(student.dob || "");
    setFormAddress(student.address || "");
    setFormRfid(student.rfid_card?.uid || "");
    setFormStatus(student.status || "active");
    
    setFormFatherName(student.parent?.father_name || "");
    setFormFatherMobile(student.parent?.father_mobile || "");
    setFormMotherName(student.parent?.mother_name || "");
    setFormMotherMobile(student.parent?.mother_mobile || "");
    
    setIsModalOpen(true);
  };

  const handleFormSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    const payload = {
      admission_number: formAdmissionNumber,
      roll_number: formRollNumber,
      name: formName,
      class_name: formClass,
      section: formSection,
      gender: formGender,
      dob: formDob,
      address: formAddress,
      rfid_uid: formRfid || null,
      status: formStatus,
      parent: {
        father_name: formFatherName,
        father_mobile: formFatherMobile,
        mother_name: formMotherName,
        mother_mobile: formMotherMobile
      }
    };

    try {
      if (formMode === "create") {
        await apiFetch("/api/students/", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        addToast("success", "Student registered successfully");
      } else {
        await apiFetch(`/api/students/${selectedStudent.id}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        addToast("success", "Student updated successfully");
      }
      setIsModalOpen(false);
      fetchStudents();
    } catch (err: any) {
      addToast("error", err.message || "Failed to submit student record");
    }
  };

  const handleDelete = async (studentId: number) => {
    if (!window.confirm("Are you sure you want to delete this student record?")) return;
    try {
      await apiFetch(`/api/students/${studentId}`, { method: "DELETE" });
      addToast("success", "Student record deleted");
      fetchStudents();
    } catch (e: any) {
      addToast("error", e.message || "Could not delete student");
    }
  };

  // Excel bulk upload
  const handleImportSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!importFile) {
      addToast("warning", "Select an Excel spreadsheet file");
      return;
    }

    const formData = new FormData();
    formData.append("file", importFile);

    try {
      const token = localStorage.getItem("spcs_token") || sessionStorage.getItem("spcs_token");
      const res = await fetch("/api/students/import/excel", {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`
        },
        body: formData
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Spreadsheet upload failed");
      }

      addToast("success", "Bulk student list imported successfully");
      setIsImportOpen(false);
      fetchStudents();
    } catch (err: any) {
      addToast("error", err.message || "Excel processing error");
    }
  };

  // QR Code mapping trigger
  const triggerQrModal = (student: any) => {
    setSelectedStudent(student);
    setIsQrOpen(true);
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900 dark:text-white">Student Directory</h1>
          <p className="text-xs text-slate-400 font-semibold">Administer student enrollment rosters, parent numbers, and RFID mappings.</p>
        </div>

        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => setIsImportOpen(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-white hover:bg-slate-50 dark:bg-slate-900 dark:hover:bg-slate-800 border border-slate-200 dark:border-slate-800 text-xs font-semibold rounded-lg transition-colors cursor-pointer"
          >
            <Upload size={12} />
            <span>Bulk Import</span>
          </button>
          <a
            href="/api/students/export/excel"
            className="flex items-center gap-1.5 px-3 py-1.5 bg-white hover:bg-slate-50 dark:bg-slate-900 dark:hover:bg-slate-800 border border-slate-200 dark:border-slate-800 text-xs font-semibold rounded-lg transition-colors cursor-pointer"
          >
            <Download size={12} />
            <span>Export Roster</span>
          </a>
          <button
            onClick={openCreateModal}
            className="flex items-center gap-1.5 px-3.5 py-1.5 bg-primary-500 hover:bg-primary-600 text-white text-xs font-semibold rounded-lg shadow-sm transition-colors cursor-pointer"
          >
            <Plus size={12} />
            <span>Add Student</span>
          </button>
        </div>
      </div>

      {/* Filters Form */}
      <div className="saas-card bg-white dark:bg-slate-900 p-5 rounded-[24px] border border-slate-200/80 dark:border-slate-800/80">
        <form onSubmit={handleSearchSubmit} className="grid grid-cols-1 sm:grid-cols-4 gap-4">
          <div className="relative">
            <span className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
              <Search size={14} />
            </span>
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search Name or ID..."
              className="block w-full pl-9 pr-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700/80 rounded-lg text-xs placeholder-slate-400 focus:outline-none focus:border-primary-500 focus:ring-4 focus:ring-primary-500/5 transition-all font-medium"
            />
          </div>
          <div>
            <select
              value={classFilter}
              onChange={(e) => setClassFilter(e.target.value)}
              className="block w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700/80 rounded-lg text-xs focus:outline-none font-medium"
            >
              <option value="">All Classes</option>
              <option value="Class 5">Class 5</option>
              <option value="Class 6">Class 6</option>
              <option value="Class 7">Class 7</option>
            </select>
          </div>
          <div>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="block w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700/80 rounded-lg text-xs focus:outline-none font-medium"
            >
              <option value="">All Statuses</option>
              <option value="active">Active</option>
              <option value="blocked">Blocked</option>
            </select>
          </div>
          <button
            type="submit"
            className="w-full py-2 bg-slate-800 hover:bg-slate-900 dark:bg-slate-700 dark:hover:bg-slate-650 text-white font-semibold text-xs rounded-lg transition-colors cursor-pointer"
          >
            Filter Records
          </button>
        </form>
      </div>

      {/* Roster Table */}
      <div className="saas-card bg-white dark:bg-slate-900 rounded-[24px] border border-slate-200/80 dark:border-slate-800/80 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50/70 dark:bg-slate-850/50 border-b border-slate-100 dark:border-slate-800 text-slate-400 dark:text-slate-500 text-[10px] font-bold uppercase tracking-wider">
                <th className="px-6 py-3.5">Admission ID</th>
                <th className="px-6 py-3.5">Name</th>
                <th className="px-6 py-3.5">Class-Sec</th>
                <th className="px-6 py-3.5">RFID UID</th>
                <th className="px-6 py-3.5">Father Contact</th>
                <th className="px-6 py-3.5">Mother Contact</th>
                <th className="px-6 py-3.5">Status</th>
                <th className="px-6 py-3.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60 text-xs">
              {loading ? (
                <tr>
                  <td colSpan={8} className="px-6 py-8 text-center text-slate-400 font-medium">
                    Loading student directory...
                  </td>
                </tr>
              ) : students.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-6 py-8 text-center text-slate-400 font-medium">
                    No student records found matching filters.
                  </td>
                </tr>
              ) : (
                students.map((st) => (
                  <tr key={st.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-850/20 transition-colors">
                    <td className="px-6 py-3.5 font-bold text-slate-700 dark:text-slate-300">{st.admission_number}</td>
                    <td className="px-6 py-3.5">
                      <div className="flex items-center gap-2">
                        <div className="w-7 h-7 rounded-full bg-primary-50 text-primary-600 flex items-center justify-center font-bold text-[10px] border border-primary-100">
                          {st.name.slice(0, 2).toUpperCase()}
                        </div>
                        <span className="font-semibold text-slate-800 dark:text-slate-200">{st.name}</span>
                      </div>
                    </td>
                    <td className="px-6 py-3.5 font-semibold text-slate-600 dark:text-slate-300">{st.class_name}-{st.section}</td>
                    <td className="px-6 py-3.5">
                      <span className={`px-2 py-0.5 rounded-md font-bold text-[10px] ${st.rfid_card ? "bg-indigo-50 text-indigo-600 border border-indigo-100 dark:bg-indigo-950/20 dark:text-indigo-400 dark:border-indigo-900/30" : "bg-rose-50 text-rose-500 border border-rose-100 dark:bg-rose-950/20 dark:text-rose-400 dark:border-rose-900/30"}`}>
                        {st.rfid_card?.uid || "Not Assigned"}
                      </span>
                    </td>
                    <td className="px-6 py-3.5 font-medium text-slate-500 dark:text-slate-400">
                      <div className="text-slate-800 dark:text-slate-200 font-semibold">{st.parent?.father_name || "N/A"}</div>
                      <div className="text-[10px] text-slate-400 mt-0.5">{st.parent?.father_mobile}</div>
                    </td>
                    <td className="px-6 py-3.5 font-medium text-slate-500 dark:text-slate-400">
                      <div className="text-slate-800 dark:text-slate-200 font-semibold">{st.parent?.mother_name || "N/A"}</div>
                      <div className="text-[10px] text-slate-400 mt-0.5">{st.parent?.mother_mobile}</div>
                    </td>
                    <td className="px-6 py-3.5">
                      <span className={`px-2 py-0.5 rounded-md text-[9px] font-bold uppercase ${
                        st.status === "active" ? "bg-emerald-50 text-emerald-600 border border-emerald-100 dark:bg-emerald-950/20 dark:text-emerald-400" : "bg-rose-50 text-rose-600 border border-rose-100 dark:bg-rose-950/20 dark:text-rose-400"
                      }`}>
                        {st.status}
                      </span>
                    </td>
                    <td className="px-6 py-3.5 text-right">
                      <div className="flex justify-end gap-1.5">
                        <button
                          onClick={() => triggerQrModal(st)}
                          title="Generate Student QR Badge"
                          className="p-1.5 bg-slate-50 hover:bg-slate-100 border border-slate-200 dark:border-slate-800 dark:bg-slate-850 dark:hover:bg-slate-750 rounded-lg text-slate-600 dark:text-slate-300 transition-colors cursor-pointer"
                        >
                          <QrCode size={12} />
                        </button>
                        <button
                          onClick={() => openEditModal(st)}
                          title="Edit Student"
                          className="p-1.5 bg-primary-50 hover:bg-primary-100 border border-primary-100 dark:bg-primary-950/20 dark:border-primary-900/30 rounded-lg text-primary-500 transition-colors cursor-pointer"
                        >
                          <Edit2 size={12} />
                        </button>
                        <button
                          onClick={() => handleDelete(st.id)}
                          title="Delete Student"
                          className="p-1.5 bg-rose-50 hover:bg-rose-100 border border-rose-100 dark:bg-rose-950/20 dark:border-rose-900/30 rounded-lg text-rose-500 transition-colors cursor-pointer"
                        >
                          <Trash2 size={12} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Footer */}
        <div className="px-6 py-4 border-t border-slate-100 dark:border-slate-800/60 flex items-center justify-between">
          <span className="text-slate-400 font-semibold text-xs">Total Records: {total}</span>
          <div className="flex items-center gap-1">
            <button
              onClick={() => setPage(Math.max(1, page - 1))}
              disabled={page === 1}
              className="p-1.5 rounded-lg border border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-850 disabled:opacity-50 cursor-pointer"
            >
              <ChevronLeft size={14} />
            </button>
            <span className="text-xs font-bold px-3 py-1 border border-slate-200 dark:border-slate-800 rounded-lg bg-slate-50 dark:bg-slate-850">{page}</span>
            <button
              onClick={() => setPage(page + 1)}
              disabled={students.length < limit}
              className="p-1.5 rounded-lg border border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-850 disabled:opacity-50 cursor-pointer"
            >
              <ChevronRight size={14} />
            </button>
          </div>
        </div>
      </div>

      {/* --- ADD / EDIT STUDENT MODAL --- */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-slate-900/30 dark:bg-black/60 backdrop-blur-xs z-50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 rounded-3xl max-w-2xl w-full max-h-[90vh] overflow-y-auto p-6 shadow-2xl border border-slate-200 dark:border-slate-800 animate-fade-in">
            <div className="flex justify-between items-center pb-4 mb-6 border-b border-slate-100 dark:border-slate-800">
              <h3 className="font-bold text-sm text-slate-800 dark:text-slate-100">{formMode === "create" ? "Add New Student Record" : "Edit Student Details"}</h3>
              <button onClick={() => setIsModalOpen(false)} className="p-1 text-slate-400 hover:bg-slate-50 rounded-full">
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleFormSubmit} className="space-y-6">
              {/* Student Profile */}
              <div>
                <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Student Profile</span>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-3">
                  <div>
                    <label className="block text-slate-400 text-[10px] uppercase font-semibold mb-1.5">Admission ID</label>
                    <input
                      type="text"
                      value={formAdmissionNumber}
                      onChange={(e) => setFormAdmissionNumber(e.target.value)}
                      className="block w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700/80 rounded-lg text-xs placeholder-slate-400 focus:outline-none focus:border-primary-500 focus:ring-4 focus:ring-primary-500/5 transition-all font-medium"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-slate-400 text-[10px] uppercase font-semibold mb-1.5">Roll Number</label>
                    <input
                      type="text"
                      value={formRollNumber}
                      onChange={(e) => setFormRollNumber(e.target.value)}
                      className="block w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700/80 rounded-lg text-xs placeholder-slate-400 focus:outline-none focus:border-primary-500 focus:ring-4 focus:ring-primary-500/5 transition-all font-medium"
                    />
                  </div>
                  <div>
                    <label className="block text-slate-400 text-[10px] uppercase font-semibold mb-1.5">Student Name</label>
                    <input
                      type="text"
                      value={formName}
                      onChange={(e) => setFormName(e.target.value)}
                      className="block w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700/80 rounded-lg text-xs placeholder-slate-400 focus:outline-none focus:border-primary-500 focus:ring-4 focus:ring-primary-500/5 transition-all font-medium"
                      required
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-3">
                  <div>
                    <label className="block text-slate-400 text-[10px] uppercase font-semibold mb-1.5">Class</label>
                    <input
                      type="text"
                      value={formClass}
                      onChange={(e) => setFormClass(e.target.value)}
                      className="block w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700/80 rounded-lg text-xs placeholder-slate-400 focus:outline-none focus:border-primary-500 focus:ring-4 focus:ring-primary-500/5 transition-all font-medium"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-slate-400 text-[10px] uppercase font-semibold mb-1.5">Section</label>
                    <input
                      type="text"
                      value={formSection}
                      onChange={(e) => setFormSection(e.target.value)}
                      className="block w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700/80 rounded-lg text-xs placeholder-slate-400 focus:outline-none focus:border-primary-500 focus:ring-4 focus:ring-primary-500/5 transition-all font-medium"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-slate-400 text-[10px] uppercase font-semibold mb-1.5">Gender</label>
                    <select
                      value={formGender}
                      onChange={(e) => setFormGender(e.target.value)}
                      className="block w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700/80 rounded-lg text-xs focus:outline-none font-medium"
                    >
                      <option value="Male">Male</option>
                      <option value="Female">Female</option>
                      <option value="Other">Other</option>
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-3">
                  <div>
                    <label className="block text-slate-400 text-[10px] uppercase font-semibold mb-1.5">Date of Birth</label>
                    <input
                      type="date"
                      value={formDob}
                      onChange={(e) => setFormDob(e.target.value)}
                      className="block w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700/80 rounded-lg text-xs focus:outline-none font-medium"
                    />
                  </div>
                  <div>
                    <label className="block text-slate-400 text-[10px] uppercase font-semibold mb-1.5">RFID Card UID</label>
                    <input
                      type="text"
                      value={formRfid}
                      onChange={(e) => setFormRfid(e.target.value)}
                      placeholder="RFID UID"
                      className="block w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700/80 rounded-lg text-xs placeholder-slate-400 focus:outline-none focus:border-primary-500 focus:ring-4 focus:ring-primary-500/5 transition-all font-medium"
                    />
                  </div>
                  <div>
                    <label className="block text-slate-400 text-[10px] uppercase font-semibold mb-1.5">Status</label>
                    <select
                      value={formStatus}
                      onChange={(e) => setFormStatus(e.target.value)}
                      className="block w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700/80 rounded-lg text-xs focus:outline-none font-medium"
                    >
                      <option value="active">Active</option>
                      <option value="blocked">Blocked</option>
                    </select>
                  </div>
                </div>

                <div className="mt-3">
                  <label className="block text-slate-400 text-[10px] uppercase font-semibold mb-1.5">Address</label>
                  <textarea
                    value={formAddress}
                    onChange={(e) => setFormAddress(e.target.value)}
                    className="block w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700/80 rounded-lg text-xs focus:outline-none font-medium"
                    rows={2}
                  ></textarea>
                </div>
              </div>

              {/* Parents Contacts Fields */}
              <div className="pt-4 border-t border-slate-100 dark:border-slate-800">
                <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Parent Contacts</span>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-3">
                  <div>
                    <label className="block text-slate-400 text-[10px] uppercase font-semibold mb-1.5">Father's Name</label>
                    <input
                      type="text"
                      value={formFatherName}
                      onChange={(e) => setFormFatherName(e.target.value)}
                      className="block w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700/80 rounded-lg text-xs placeholder-slate-400 focus:outline-none focus:border-primary-500 focus:ring-4 focus:ring-primary-500/5 transition-all font-medium"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-slate-400 text-[10px] uppercase font-semibold mb-1.5">Father's Mobile Number</label>
                    <input
                      type="text"
                      value={formFatherMobile}
                      onChange={(e) => setFormFatherMobile(e.target.value)}
                      className="block w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700/80 rounded-lg text-xs placeholder-slate-400 focus:outline-none focus:border-primary-500 focus:ring-4 focus:ring-primary-500/5 transition-all font-medium"
                      required
                    />
                  </div>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-3">
                  <div>
                    <label className="block text-slate-400 text-[10px] uppercase font-semibold mb-1.5">Mother's Name</label>
                    <input
                      type="text"
                      value={formMotherName}
                      onChange={(e) => setFormMotherName(e.target.value)}
                      className="block w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700/80 rounded-lg text-xs placeholder-slate-400 focus:outline-none focus:border-primary-500 focus:ring-4 focus:ring-primary-500/5 transition-all font-medium"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-slate-400 text-[10px] uppercase font-semibold mb-1.5">Mother's Mobile Number</label>
                    <input
                      type="text"
                      value={formMotherMobile}
                      onChange={(e) => setFormMotherMobile(e.target.value)}
                      className="block w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700/80 rounded-lg text-xs placeholder-slate-400 focus:outline-none focus:border-primary-500 focus:ring-4 focus:ring-primary-500/5 transition-all font-medium"
                      required
                    />
                  </div>
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-slate-100 dark:border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 border border-slate-200 dark:border-slate-700 text-xs font-semibold rounded-lg text-slate-600 dark:text-slate-300 cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 bg-primary-500 hover:bg-primary-600 text-white text-xs font-semibold rounded-lg shadow-sm transition-colors cursor-pointer"
                >
                  Save Record
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* --- BULK IMPORT MODAL --- */}
      {isImportOpen && (
        <div className="fixed inset-0 bg-slate-900/30 dark:bg-black/60 backdrop-blur-xs z-50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 rounded-3xl max-w-md w-full p-6 shadow-2xl border border-slate-200 dark:border-slate-800">
            <div className="flex justify-between items-center pb-4 mb-4 border-b border-slate-100 dark:border-slate-800">
              <h3 className="font-bold text-sm text-slate-800 dark:text-slate-100">Bulk Import Students</h3>
              <button onClick={() => setIsImportOpen(false)} className="p-1 text-slate-400 hover:bg-slate-50 rounded-full">
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleImportSubmit} className="space-y-4">
              <div className="border border-dashed border-slate-200 dark:border-slate-800 rounded-2xl p-6 text-center">
                <FileSpreadsheet className="mx-auto text-primary-500 mb-3" size={32} />
                <label className="block text-xs font-semibold text-slate-500 mb-2 cursor-pointer">
                  <span>Upload Excel Spreadsheet (.xlsx, .xls)</span>
                  <input
                    type="file"
                    accept=".xlsx, .xls"
                    onChange={(e) => setImportFile(e.target.files ? e.target.files[0] : null)}
                    className="hidden"
                  />
                </label>
                {importFile && (
                  <p className="text-xs font-bold text-indigo-600 mt-2">{importFile.name}</p>
                )}
              </div>

              <div className="flex gap-2">
                <a
                  href="/templates/student_import_template.xlsx"
                  download
                  className="flex-1 py-2 border border-slate-200 dark:border-slate-700 text-center font-bold text-[10px] text-slate-500 uppercase rounded-xl hover:bg-slate-50"
                >
                  Get Template
                </a>
                <button
                  type="submit"
                  className="flex-1 py-2 bg-primary-500 hover:bg-primary-600 text-white font-bold text-[10px] uppercase rounded-xl shadow-md cursor-pointer"
                >
                  Upload File
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* --- QR BADGE DETAIL MODAL --- */}
      {isQrOpen && selectedStudent && (
        <div className="fixed inset-0 bg-slate-900/30 dark:bg-black/60 backdrop-blur-xs z-50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 rounded-3xl max-w-xs w-full p-6 shadow-2xl border border-slate-200 dark:border-slate-800 text-center relative">
            <button onClick={() => setIsQrOpen(false)} className="absolute top-4 right-4 p-1 text-slate-400 hover:bg-slate-50 rounded-full">
              <X size={16} />
            </button>
            
            <h3 className="font-bold text-sm text-slate-800 dark:text-slate-100 mb-4">Student ID Badge Mapping</h3>

            <div className="bg-slate-50 dark:bg-slate-950 p-4 rounded-2xl flex items-center justify-center border border-slate-100 dark:border-slate-800 mb-4">
              <img
                src={`https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=${selectedStudent.admission_number}`}
                alt="Student QR Badge"
                className="w-40 h-40 object-contain shadow-sm border border-slate-100 dark:border-slate-800"
              />
            </div>

            <h4 className="font-bold text-sm text-slate-800 dark:text-slate-200">{selectedStudent.name}</h4>
            <p className="text-xs text-slate-400 font-semibold mt-1">Adm: {selectedStudent.admission_number}</p>
            <p className="text-[10px] text-slate-400 font-bold bg-slate-50 dark:bg-slate-800 px-2.5 py-0.5 rounded-md inline-block mt-2 uppercase">
              {selectedStudent.class_name} - {selectedStudent.section}
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
