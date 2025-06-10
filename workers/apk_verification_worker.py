#!/usr/bin/env python3
"""
APK Development Verification Worker
Ensures our Android APK build process follows best practices
Based on Android Gradle Recipes and official documentation
"""

import os
import json
import time
import subprocess
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile
import shutil
import re

from workers.base_worker import BaseWorker


class APKVerificationWorker(BaseWorker):
    """
    Verifies Android APK development process against official patterns
    Ensures compliance with Android/Gradle best practices
    """
    
    def __init__(self, worker_id: str = "apk_verification_worker", **kwargs):
        super().__init__(worker_id, **kwargs)
        self.verification_results = []
        self.gradle_patterns = self._load_gradle_patterns()
        self.buildozer_patterns = self._load_buildozer_patterns()
        
    def _load_gradle_patterns(self) -> Dict[str, Any]:
        """Load official Android Gradle patterns"""
        return {
            "build_structure": {
                "required_files": [
                    "build.gradle",
                    "build.gradle.kts",
                    "settings.gradle",
                    "gradle.properties",
                    "gradlew",
                    "gradlew.bat"
                ],
                "gradle_wrapper": "gradle/wrapper/gradle-wrapper.properties",
                "min_gradle_version": "7.0",
                "recommended_gradle_version": "8.0"
            },
            "agp_configuration": {
                "min_version": "7.0.0",
                "recommended_version": "8.0.0",
                "build_features": {
                    "buildConfig": "Enable for BuildConfig generation",
                    "viewBinding": "For type-safe view references",
                    "compose": "For Jetpack Compose"
                },
                "variant_configuration": {
                    "debug": {
                        "minifyEnabled": False,
                        "shrinkResources": False,
                        "debuggable": True
                    },
                    "release": {
                        "minifyEnabled": True,
                        "shrinkResources": True,
                        "debuggable": False,
                        "signingConfig": "Required for release"
                    }
                }
            },
            "dependencies": {
                "implementation_vs_api": "Use implementation for internal dependencies",
                "version_catalog": "Use libs.versions.toml for centralized versions",
                "bom_usage": "Use BOMs for consistent versions"
            },
            "best_practices": {
                "gradle_tasks": [
                    "assembleDebug",
                    "assembleRelease",
                    "testDebugUnitTest",
                    "connectedAndroidTest"
                ],
                "performance": {
                    "configuration_cache": True,
                    "parallel_execution": True,
                    "build_cache": True
                },
                "artifact_handling": {
                    "single_artifact": "For APK manipulation",
                    "multiple_artifact": "For native debug symbols",
                    "scoped_artifacts": "For class transformations"
                }
            }
        }
    
    def _load_buildozer_patterns(self) -> Dict[str, Any]:
        """Load Buildozer/Python-for-Android patterns"""
        return {
            "spec_configuration": {
                "required_fields": [
                    "title",
                    "package.name",
                    "package.domain",
                    "source.dir",
                    "version",
                    "requirements"
                ],
                "android_specific": {
                    "api": {
                        "min": 21,
                        "target": 31,
                        "recommended": 33
                    },
                    "ndk": {
                        "recommended": "25b",
                        "supported": ["23b", "24", "25b"]
                    },
                    "arch": {
                        "default": "arm64-v8a",
                        "supported": ["armeabi-v7a", "arm64-v8a", "x86", "x86_64"]
                    }
                },
                "permissions": {
                    "required": ["INTERNET"],
                    "storage": ["WRITE_EXTERNAL_STORAGE", "READ_EXTERNAL_STORAGE"],
                    "camera": ["CAMERA"],
                    "location": ["ACCESS_FINE_LOCATION", "ACCESS_COARSE_LOCATION"]
                }
            },
            "build_process": {
                "p4a_bootstrap": {
                    "sdl2": "For games and multimedia",
                    "webview": "For web-based apps",
                    "service_only": "For background services"
                },
                "optimization": {
                    "release": True,
                    "strip_symbols": True,
                    "optimize_size": True
                },
                "common_issues": {
                    "missing_recipe": "Check python-for-android recipes",
                    "ndk_not_found": "Set ANDROID_NDK_HOME",
                    "api_mismatch": "Ensure API levels are compatible",
                    "arch_mismatch": "Check device architecture"
                }
            }
        }
    
    def verify_project_structure(self, project_path: str) -> Dict[str, Any]:
        """Verify Android project structure"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "checks": [],
            "structure_score": 0,
            "issues": [],
            "recommendations": []
        }
        
        project_dir = Path(project_path)
        
        # Check 1: Buildozer spec file
        spec_check = self._verify_buildozer_spec(project_dir)
        results["checks"].append(spec_check)
        
        # Check 2: Source structure
        source_check = self._verify_source_structure(project_dir)
        results["checks"].append(source_check)
        
        # Check 3: Assets and resources
        assets_check = self._verify_assets(project_dir)
        results["checks"].append(assets_check)
        
        # Check 4: Dependencies
        deps_check = self._verify_dependencies(project_dir)
        results["checks"].append(deps_check)
        
        # Check 5: Build configuration
        build_check = self._verify_build_config(project_dir)
        results["checks"].append(build_check)
        
        # Calculate structure score
        passed_checks = sum(1 for check in results["checks"] if check["passed"])
        total_checks = len(results["checks"])
        results["structure_score"] = (passed_checks / total_checks) * 100
        
        # Generate recommendations
        results["recommendations"] = self._generate_project_recommendations(results)
        
        return results
    
    def _verify_buildozer_spec(self, project_dir: Path) -> Dict[str, Any]:
        """Verify buildozer.spec configuration"""
        check = {
            "name": "Buildozer Specification",
            "passed": True,
            "details": []
        }
        
        spec_file = project_dir / "buildozer.spec"
        if not spec_file.exists():
            check["passed"] = False
            check["details"].append("❌ buildozer.spec not found")
            return check
        
        # Parse spec file
        import configparser
        config = configparser.ConfigParser()
        try:
            config.read(spec_file)
            
            # Check required fields
            required = self.buildozer_patterns["spec_configuration"]["required_fields"]
            app_section = config["app"] if "app" in config else {}
            
            for field in required:
                if field in app_section:
                    check["details"].append(f"✅ {field} configured")
                else:
                    check["passed"] = False
                    check["details"].append(f"❌ Missing {field}")
            
            # Check Android API levels
            if "android.api" in app_section:
                api_level = int(app_section.get("android.api", "0"))
                min_api = self.buildozer_patterns["spec_configuration"]["android_specific"]["api"]["min"]
                if api_level >= min_api:
                    check["details"].append(f"✅ API level {api_level} (>= {min_api})")
                else:
                    check["passed"] = False
                    check["details"].append(f"❌ API level {api_level} too low (min: {min_api})")
            
            # Check architecture
            if "android.arch" in app_section:
                arch = app_section.get("android.arch", "")
                supported = self.buildozer_patterns["spec_configuration"]["android_specific"]["arch"]["supported"]
                if arch in supported:
                    check["details"].append(f"✅ Architecture: {arch}")
                else:
                    check["details"].append(f"⚠️ Architecture {arch} may have limited support")
            
            # Check permissions
            if "android.permissions" in app_section:
                permissions = app_section.get("android.permissions", "").split(",")
                if "INTERNET" in permissions:
                    check["details"].append("✅ INTERNET permission included")
                else:
                    check["details"].append("⚠️ INTERNET permission missing")
            
        except Exception as e:
            check["passed"] = False
            check["details"].append(f"❌ Failed to parse spec: {str(e)}")
        
        return check
    
    def _verify_source_structure(self, project_dir: Path) -> Dict[str, Any]:
        """Verify source code structure"""
        check = {
            "name": "Source Structure",
            "passed": True,
            "details": []
        }
        
        # Check main.py
        main_py = project_dir / "main.py"
        if main_py.exists():
            check["details"].append("✅ main.py found")
            
            # Verify main.py content
            with open(main_py, 'r') as f:
                content = f.read()
                
            # Check for Kivy/KivyMD app
            if "MDApp" in content or "App" in content:
                check["details"].append("✅ Kivy app class found")
            else:
                check["details"].append("⚠️ No Kivy app class found")
            
            # Check for Android imports
            if "android" in content or "jnius" in content:
                check["details"].append("✅ Android imports present")
            
            # Check for permissions handling
            if "request_permissions" in content:
                check["details"].append("✅ Permission handling implemented")
        else:
            check["passed"] = False
            check["details"].append("❌ main.py not found")
        
        # Check package structure
        important_dirs = ["screens", "services", "utils", "workers"]
        for dir_name in important_dirs:
            dir_path = project_dir / dir_name
            if dir_path.exists() and dir_path.is_dir():
                check["details"].append(f"✅ {dir_name}/ directory found")
                
                # Check for __init__.py
                init_file = dir_path / "__init__.py"
                if not init_file.exists():
                    check["details"].append(f"⚠️ {dir_name}/__init__.py missing")
        
        return check
    
    def _verify_assets(self, project_dir: Path) -> Dict[str, Any]:
        """Verify assets and resources"""
        check = {
            "name": "Assets & Resources",
            "passed": True,
            "details": []
        }
        
        # Check icon
        icon_files = ["icon.png", "assets/icon.png"]
        icon_found = False
        for icon_path in icon_files:
            if (project_dir / icon_path).exists():
                icon_found = True
                check["details"].append(f"✅ Icon found: {icon_path}")
                
                # Verify icon dimensions
                try:
                    from PIL import Image
                    with Image.open(project_dir / icon_path) as img:
                        width, height = img.size
                        if width >= 512 and height >= 512:
                            check["details"].append(f"✅ Icon size: {width}x{height}")
                        else:
                            check["details"].append(f"⚠️ Icon size {width}x{height} (recommend 512x512+)")
                except:
                    pass
                break
        
        if not icon_found:
            check["passed"] = False
            check["details"].append("❌ No icon.png found")
        
        # Check presplash
        presplash_files = ["presplash.png", "assets/presplash.png"]
        presplash_found = False
        for presplash_path in presplash_files:
            if (project_dir / presplash_path).exists():
                presplash_found = True
                check["details"].append(f"✅ Presplash found: {presplash_path}")
                break
        
        if not presplash_found:
            check["details"].append("⚠️ No presplash.png found (optional)")
        
        # Check data directory
        if (project_dir / "data").exists():
            check["details"].append("✅ data/ directory found")
        
        return check
    
    def _verify_dependencies(self, project_dir: Path) -> Dict[str, Any]:
        """Verify dependencies configuration"""
        check = {
            "name": "Dependencies",
            "passed": True,
            "details": []
        }
        
        # Check requirements.txt
        req_file = project_dir / "requirements.txt"
        if req_file.exists():
            check["details"].append("✅ requirements.txt found")
            
            with open(req_file, 'r') as f:
                requirements = f.read().splitlines()
            
            # Check for essential dependencies
            essential = ["kivy", "kivymd", "pillow", "requests"]
            for dep in essential:
                if any(dep in req.lower() for req in requirements):
                    check["details"].append(f"✅ {dep} in requirements")
            
            # Check for version pinning
            pinned = sum(1 for req in requirements if "==" in req)
            if pinned > 0:
                check["details"].append(f"✅ {pinned} dependencies version-pinned")
            else:
                check["details"].append("⚠️ No version pinning found")
        else:
            check["passed"] = False
            check["details"].append("❌ requirements.txt not found")
        
        # Check buildozer spec requirements
        spec_file = project_dir / "buildozer.spec"
        if spec_file.exists():
            import configparser
            config = configparser.ConfigParser()
            try:
                config.read(spec_file)
                if "app" in config and "requirements" in config["app"]:
                    spec_reqs = config["app"]["requirements"]
                    check["details"].append("✅ Requirements in buildozer.spec")
                    
                    # Check for p4a recipes
                    if "python3" in spec_reqs:
                        check["details"].append("✅ python3 recipe included")
                    
                    # Check for Android-specific
                    if "android" in spec_reqs or "pyjnius" in spec_reqs:
                        check["details"].append("✅ Android dependencies included")
            except:
                pass
        
        return check
    
    def _verify_build_config(self, project_dir: Path) -> Dict[str, Any]:
        """Verify build configuration"""
        check = {
            "name": "Build Configuration",
            "passed": True,
            "details": []
        }
        
        # Check for build scripts
        build_scripts = ["build.sh", "build_apk.sh", "build_dalle2_complete.sh"]
        script_found = False
        for script in build_scripts:
            if (project_dir / script).exists():
                script_found = True
                check["details"].append(f"✅ Build script found: {script}")
                
                # Check script content
                with open(project_dir / script, 'r') as f:
                    content = f.read()
                
                # Check for best practices
                if "buildozer -v" in content:
                    check["details"].append("✅ Verbose build logging enabled")
                
                if "buildozer android clean" in content:
                    check["details"].append("✅ Clean build step included")
                
                if "source venv/bin/activate" in content:
                    check["details"].append("✅ Virtual environment used")
                
                if "JAVA_HOME" in content:
                    check["details"].append("✅ Java configuration included")
                
                break
        
        if not script_found:
            check["details"].append("⚠️ No build script found")
        
        # Check for CI/CD configuration
        ci_files = [".github/workflows/build.yml", ".gitlab-ci.yml", "bitrise.yml"]
        for ci_file in ci_files:
            if (project_dir / ci_file).exists():
                check["details"].append(f"✅ CI/CD config found: {ci_file}")
                break
        
        return check
    
    def verify_apk_build_process(self, build_log_path: str) -> Dict[str, Any]:
        """Verify APK build process from logs"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "build_stages": [],
            "issues": [],
            "warnings": [],
            "success": False
        }
        
        if not os.path.exists(build_log_path):
            results["issues"].append("Build log not found")
            return results
        
        with open(build_log_path, 'r') as f:
            log_content = f.read()
        
        # Check build stages
        stages = [
            ("Check requirements", "Check requirements for android"),
            ("Install platform", "Install platform"),
            ("Compile platform", "Compile platform"),
            ("Build application", "Build the application"),
            ("Package application", "Package the application"),
            ("APK creation", "BUILD SUCCESSFUL")
        ]
        
        for stage_name, pattern in stages:
            if pattern in log_content:
                results["build_stages"].append({
                    "name": stage_name,
                    "completed": True
                })
            else:
                results["build_stages"].append({
                    "name": stage_name,
                    "completed": False
                })
        
        # Check for common issues
        if "BUILD FAILED" in log_content:
            results["success"] = False
            results["issues"].append("Build failed")
        elif "BUILD SUCCESSFUL" in log_content:
            results["success"] = True
        
        # Extract warnings
        warning_patterns = [
            "WARNING:",
            "deprecated",
            "Conflict",
            "Missing"
        ]
        
        for pattern in warning_patterns:
            if pattern in log_content:
                # Extract context around warning
                lines = log_content.split('\n')
                for i, line in enumerate(lines):
                    if pattern in line:
                        context = lines[max(0, i-1):min(len(lines), i+2)]
                        results["warnings"].append('\n'.join(context))
        
        return results
    
    def verify_apk_content(self, apk_path: str) -> Dict[str, Any]:
        """Verify APK content and structure"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "apk_info": {},
            "content_checks": [],
            "security_checks": [],
            "optimization_score": 0
        }
        
        if not os.path.exists(apk_path):
            results["content_checks"].append({
                "name": "APK File",
                "passed": False,
                "details": "APK file not found"
            })
            return results
        
        # Get APK info
        results["apk_info"] = {
            "size": os.path.getsize(apk_path) / (1024 * 1024),  # MB
            "filename": os.path.basename(apk_path)
        }
        
        # Extract and analyze APK
        try:
            with zipfile.ZipFile(apk_path, 'r') as apk:
                file_list = apk.namelist()
                
                # Check 1: AndroidManifest.xml
                if "AndroidManifest.xml" in file_list:
                    results["content_checks"].append({
                        "name": "AndroidManifest.xml",
                        "passed": True,
                        "details": "Manifest present"
                    })
                else:
                    results["content_checks"].append({
                        "name": "AndroidManifest.xml",
                        "passed": False,
                        "details": "Manifest missing"
                    })
                
                # Check 2: DEX files
                dex_files = [f for f in file_list if f.endswith('.dex')]
                results["content_checks"].append({
                    "name": "DEX Files",
                    "passed": len(dex_files) > 0,
                    "details": f"Found {len(dex_files)} DEX files"
                })
                
                # Check 3: Native libraries
                lib_files = [f for f in file_list if f.startswith('lib/')]
                arch_dirs = set(f.split('/')[1] for f in lib_files if len(f.split('/')) > 1)
                results["content_checks"].append({
                    "name": "Native Libraries",
                    "passed": len(lib_files) > 0,
                    "details": f"Architectures: {', '.join(arch_dirs)}"
                })
                
                # Check 4: Resources
                res_files = [f for f in file_list if f.startswith('res/')]
                results["content_checks"].append({
                    "name": "Resources",
                    "passed": len(res_files) > 0,
                    "details": f"Found {len(res_files)} resource files"
                })
                
                # Check 5: Assets
                asset_files = [f for f in file_list if f.startswith('assets/')]
                results["content_checks"].append({
                    "name": "Assets",
                    "passed": True,
                    "details": f"Found {len(asset_files)} asset files"
                })
                
                # Security checks
                # Check 1: Signing
                if "META-INF/CERT.RSA" in file_list or "META-INF/CERT.SF" in file_list:
                    results["security_checks"].append({
                        "name": "APK Signing",
                        "passed": True,
                        "details": "APK is signed"
                    })
                else:
                    results["security_checks"].append({
                        "name": "APK Signing",
                        "passed": False,
                        "details": "APK is not signed"
                    })
                
                # Check 2: Debug mode
                debug_indicators = ["debug", "test"]
                is_debug = any(indicator in apk_path.lower() for indicator in debug_indicators)
                results["security_checks"].append({
                    "name": "Build Type",
                    "passed": True,
                    "details": "Debug build" if is_debug else "Release build"
                })
                
                # Calculate optimization score
                total_size = results["apk_info"]["size"]
                if total_size < 10:
                    optimization_score = 100
                elif total_size < 25:
                    optimization_score = 80
                elif total_size < 50:
                    optimization_score = 60
                elif total_size < 100:
                    optimization_score = 40
                else:
                    optimization_score = 20
                
                results["optimization_score"] = optimization_score
                
        except Exception as e:
            results["content_checks"].append({
                "name": "APK Analysis",
                "passed": False,
                "details": f"Failed to analyze APK: {str(e)}"
            })
        
        return results
    
    def _generate_project_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate project structure recommendations"""
        recommendations = []
        
        if results["structure_score"] < 100:
            recommendations.append("🔧 Address failing checks to improve project structure")
        
        # Buildozer-specific recommendations
        recommendations.extend([
            "📱 Test on multiple Android versions (API 21-33)",
            "🏗️ Use arm64-v8a for modern devices",
            "📦 Keep APK size under 25MB for better distribution",
            "🔐 Sign release APKs with proper keystore",
            "⚡ Enable ProGuard/R8 for release builds",
            "📊 Use Android Studio Profiler for performance",
            "🧪 Implement unit tests with pytest",
            "📝 Add comprehensive logging for debugging",
            "🌐 Handle offline scenarios gracefully",
            "🔄 Implement proper state management"
        ])
        
        # Best practices from Android Gradle Recipes
        recommendations.extend([
            "🎯 Use variant-specific configurations",
            "🔧 Leverage AGP's artifact API for transformations",
            "📦 Implement dependency substitution for testing",
            "🏃 Enable configuration caching for faster builds",
            "🔍 Use lint checks for code quality",
            "📊 Generate build reports for optimization"
        ])
        
        return recommendations
    
    def generate_apk_compliance_report(self, project_path: str, apk_path: Optional[str] = None) -> str:
        """Generate comprehensive APK development compliance report"""
        report = []
        report.append("=" * 60)
        report.append("ANDROID APK DEVELOPMENT COMPLIANCE REPORT")
        report.append("=" * 60)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Project Structure Verification
        structure_results = self.verify_project_structure(project_path)
        report.append("## PROJECT STRUCTURE VERIFICATION")
        report.append(f"Structure Score: {structure_results['structure_score']:.1f}%")
        report.append("")
        
        for check in structure_results["checks"]:
            status = "✅ PASS" if check["passed"] else "❌ FAIL"
            report.append(f"{status} - {check['name']}")
            for detail in check["details"]:
                report.append(f"  {detail}")
            report.append("")
        
        # APK Content Verification (if APK provided)
        if apk_path and os.path.exists(apk_path):
            apk_results = self.verify_apk_content(apk_path)
            report.append("## APK CONTENT VERIFICATION")
            report.append(f"APK Size: {apk_results['apk_info'].get('size', 0):.2f} MB")
            report.append(f"Optimization Score: {apk_results['optimization_score']}%")
            report.append("")
            
            report.append("### Content Checks")
            for check in apk_results["content_checks"]:
                status = "✅ PASS" if check["passed"] else "❌ FAIL"
                report.append(f"{status} - {check['name']}: {check['details']}")
            report.append("")
            
            report.append("### Security Checks")
            for check in apk_results["security_checks"]:
                status = "✅ PASS" if check["passed"] else "❌ FAIL"
                report.append(f"{status} - {check['name']}: {check['details']}")
            report.append("")
        
        # Recommendations
        report.append("## RECOMMENDATIONS")
        all_recommendations = structure_results["recommendations"]
        for i, rec in enumerate(all_recommendations, 1):
            report.append(f"{i}. {rec}")
        
        report.append("")
        report.append("## BUILDOZER BEST PRACTICES")
        report.append("1. Always use virtual environment")
        report.append("2. Pin dependency versions")
        report.append("3. Test on physical devices")
        report.append("4. Monitor build logs for warnings")
        report.append("5. Use release mode for production")
        report.append("6. Implement proper error handling")
        report.append("7. Follow Material Design guidelines")
        report.append("8. Optimize images and assets")
        report.append("9. Implement proper permissions flow")
        report.append("10. Test on different screen sizes")
        
        report.append("")
        report.append("## ANDROID GRADLE PATTERNS REFERENCE")
        report.append("Based on Android Gradle Recipes:")
        report.append("- Use onVariants for variant configuration")
        report.append("- Implement artifact transformations")
        report.append("- Leverage finalizeDsl for DSL modifications")
        report.append("- Use registerPreBuild for validation")
        report.append("- Implement proper signing configuration")
        report.append("- Use build features selectively")
        
        return "\n".join(report)
    
    def process_task(self, task):
        """Process tasks (not used in this worker)"""
        pass
    
    def _process_message(self, message):
        """Process verification requests"""
        if message.msg_type == "VERIFY_PROJECT":
            project_path = message.data.get("project_path")
            if project_path:
                results = self.verify_project_structure(project_path)
                self._send_message("main", "PROJECT_VERIFICATION_COMPLETE", results)
        
        elif message.msg_type == "VERIFY_BUILD":
            build_log = message.data.get("build_log")
            if build_log:
                results = self.verify_apk_build_process(build_log)
                self._send_message("main", "BUILD_VERIFICATION_COMPLETE", results)
        
        elif message.msg_type == "VERIFY_APK":
            apk_path = message.data.get("apk_path")
            if apk_path:
                results = self.verify_apk_content(apk_path)
                self._send_message("main", "APK_VERIFICATION_COMPLETE", results)
        
        elif message.msg_type == "GENERATE_APK_REPORT":
            project_path = message.data.get("project_path")
            apk_path = message.data.get("apk_path")
            if project_path:
                report = self.generate_apk_compliance_report(project_path, apk_path)
                
                # Save report
                report_path = Path(self.app_data_dir) / "apk_reports"
                report_path.mkdir(exist_ok=True)
                
                filename = f"apk_compliance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                filepath = report_path / filename
                
                with open(filepath, 'w') as f:
                    f.write(report)
                
                self._send_message("main", "APK_REPORT_GENERATED", {
                    "report": report,
                    "filepath": str(filepath)
                })


# Standalone verification functions
def verify_buildozer_spec(spec_content: str) -> Tuple[bool, List[str]]:
    """Verify buildozer.spec content"""
    issues = []
    valid = True
    
    required_fields = [
        "[app]",
        "title =",
        "package.name =",
        "package.domain =",
        "source.dir =",
        "version =",
        "requirements ="
    ]
    
    for field in required_fields:
        if field not in spec_content:
            issues.append(f"Missing required field: {field}")
            valid = False
    
    # Check Android configuration
    if "android.api" in spec_content:
        try:
            api_match = re.search(r'android\.api\s*=\s*(\d+)', spec_content)
            if api_match:
                api_level = int(api_match.group(1))
                if api_level < 21:
                    issues.append(f"API level {api_level} too low (minimum: 21)")
                    valid = False
        except:
            pass
    else:
        issues.append("Missing android.api configuration")
        valid = False
    
    # Check permissions
    if "android.permissions" not in spec_content:
        issues.append("No permissions specified")
    elif "INTERNET" not in spec_content:
        issues.append("INTERNET permission should be included")
    
    return valid, issues


def verify_gradle_build(build_gradle_content: str) -> Tuple[bool, List[str]]:
    """Verify build.gradle configuration"""
    issues = []
    valid = True
    
    # Check for Android plugin
    if "com.android.application" not in build_gradle_content:
        issues.append("Missing Android application plugin")
        valid = False
    
    # Check for build features
    if "buildFeatures" in build_gradle_content:
        if "buildConfig = true" not in build_gradle_content:
            issues.append("BuildConfig generation not enabled")
    
    # Check for signing config
    if "signingConfigs" not in build_gradle_content:
        issues.append("No signing configuration found")
    
    # Check for ProGuard/R8
    if "release" in build_gradle_content:
        if "minifyEnabled true" not in build_gradle_content:
            issues.append("Code minification not enabled for release")
        if "shrinkResources true" not in build_gradle_content:
            issues.append("Resource shrinking not enabled for release")
    
    return valid, issues


if __name__ == "__main__":
    # Test verification
    print("Android APK Development Verification Worker")
    print("=" * 40)
    
    # Test buildozer spec verification
    test_spec = """
[app]
title = DALL-E 2 Complete
package.name = dalle2complete
package.domain = com.aiart
source.dir = .
version = 2.0
requirements = python3,kivy,kivymd
android.api = 31
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE
"""
    
    valid, issues = verify_buildozer_spec(test_spec)
    print(f"Buildozer spec valid: {valid}")
    if issues:
        print("Issues found:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("No issues found!")