"""
Auditor package for NEAR smart contract code auditing.
"""

try:
    from .auditor import CodeAuditor
    __all__ = ['CodeAuditor']
except ImportError:
    # Fallback for direct execution
    import os
    import importlib.util
    auditor_path = os.path.join(os.path.dirname(__file__), 'auditor.py')
    if os.path.exists(auditor_path):
        spec = importlib.util.spec_from_file_location("auditor", auditor_path)
        auditor_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(auditor_module)
        CodeAuditor = auditor_module.CodeAuditor
        __all__ = ['CodeAuditor']
    else:
        __all__ = []