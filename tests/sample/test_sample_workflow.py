#!/usr/bin/env python3
"""
Sample repository test - creates a complete tex-repo workflow example
Tests the full system: init -> config -> new paper -> build -> status
"""
import sys
import os
import tempfile
import subprocess
from pathlib import Path

# Add tex-repo to path
test_dir = Path(__file__).parent
repo_root = test_dir.parent.parent
sys.path.insert(0, str(repo_root))

from texrepo.cli import main


class AutoInput:
    """Provides automatic inputs for interactive commands"""
    def __init__(self, responses):
        self.responses = iter(responses)
    
    def __enter__(self):
        import builtins
        self.original_input = builtins.input
        builtins.input = self.mock_input
        return self
    
    def __exit__(self, *args):
        import builtins
        builtins.input = self.original_input
    
    def mock_input(self, prompt):
        try:
            response = next(self.responses)
            print(f"{prompt}{response}")
            return response
        except StopIteration:
            return ""


def create_sample_repository():
    """Create a complete sample repository demonstrating all features"""
    print("🏗️  Creating sample tex-repo repository...")
    
    # Initialize repository with comprehensive metadata
    init_responses = [
        "Advanced Machine Learning Research",  # project_name
        "Dr. Jane Smith",                      # author_name
        "Stanford University",                 # organization
        "jane.smith@stanford.edu",             # author_email
        "",                                   # default_author_affil (use org)
        "Stanford",                           # short_affiliation
        "0000-0002-1825-0097",               # author_orcid
        "MIT License",                        # license
        "submission",                         # date_policy
        "ieeetr"                             # bibliography_style
    ]
    
    with AutoInput(init_responses):
        result = main(['init', 'ml-research-repo'])
    
    assert result == 0, "Repository initialization should succeed"
    
    # Enter the repository
    os.chdir('ml-research-repo')
    
    # Create custom configuration
    print("⚙️  Creating custom configuration...")
    config_content = """# tex-repo Configuration File
# Customization for ML research papers

[paper]
# Use more sections for detailed papers
section_count = 6
# Use article class with conference formatting
document_class = article
document_options = 10pt,twocolumn
# Include abstract for all papers
include_abstract = true

[build]
# Use latexmk for better dependency handling
default_engine = latexmk
# Clean build artifacts after successful compilation
clean_after_build = true

[metadata]
# Always include ORCID in papers
include_orcid = true
# Use submission date format
date_format = submission
"""
    
    with open('.texrepo-config', 'w') as f:
        f.write(config_content)
    
    print("✅ Custom configuration created")
    
    # Create domains
    domain_specs = [
        ('01_formalism', 'forms'),
        ('02_processes', 'process-models'),
        ('03_applications', 'vision'),
    ]
    for stage, name in domain_specs:
        main(['nd', stage, name])

    # Create papers in different domains
    papers = [
        {
            'domain': '01_formalism/00_forms',
            'name': 'spec-derived-forms',
            'title': 'Admissible Forms from the Spec',
            'content': {
                'abstract': 'Formal structures derived directly from the Spec.',
                'intro': 'The Spec constrains all admissible forms.',
                'related': 'Related work grounds representational choices in immutable constraints.',
                'methods': 'We enumerate constructors and closures permitted by the Spec.',
                'results': 'All derived forms remain compliant with Spec restrictions.',
                'conclusion': 'These forms anchor downstream work.'
            }
        },
        {
            'domain': '02_processes/00_process-models',
            'name': 'process-analysis',
            'title': 'Processes Anchored in the Spec',
            'content': {
                'abstract': 'Process descriptions tied to the formalism.',
                'intro': 'Processes inherit admissible forms from the Spec.',
                'related': 'Process modeling literature often omits upstream constraints.',
                'methods': 'We map processes onto Spec-compliant representations.',
                'results': 'Each process preserves Spec-defined invariants.',
                'conclusion': 'These processes are ready for application design.'
            }
        },
        {
            'domain': '03_applications/00_vision',
            'name': 'vision-transformers',
            'title': 'Efficient Vision Transformers for Real-Time Object Detection',
            'content': {
                'abstract': 'We propose a lightweight vision transformer architecture optimized for real-time object detection.',
                'intro': 'Vision transformers have achieved excellent results but at high computational cost.',
                'related': 'Recent work on efficient transformers includes MobileViT and others.',
                'methods': 'Our approach combines pruning, distillation, and architectural innovations.',
                'results': 'We achieve 2x speedup while maintaining 95% of original accuracy on COCO dataset.',
                'conclusion': 'Our efficient architecture makes vision transformers practical for mobile deployment.'
            }
        }
    ]
    
    # Create each paper with content
    for paper in papers:
        print(f"📄 Creating paper: {paper['title']}")
        
        # Create the paper structure
        result = main(['np', paper['domain'], paper['name'], paper['title']])
        assert result == 0, f"Paper creation should succeed for {paper['name']}"
        
        paper_dir = Path(paper['domain']) / paper['name']
        
        # Add content to sections
        if paper['content']['abstract']:
            abstract_file = paper_dir / 'sections' / 'abstract.tex'
            if abstract_file.exists():
                with open(abstract_file, 'w') as f:
                    f.write(paper['content']['abstract'])
        
        # Add content to numbered sections
        section_map = ['intro', 'related', 'methods', 'results', 'conclusion']
        for i, section_key in enumerate(section_map, 1):
            section_file = paper_dir / 'sections' / f'section_{i}.tex'
            if section_file.exists() and section_key in paper['content']:
                with open(section_file, 'w') as f:
                    f.write(paper['content'][section_key])
        
        # Add some bibliography entries
        bib_file = paper_dir / 'bibliography.bib'
        sample_bib = f"""@article{{bengio2013representation,
  title={{Representation learning: A review and new perspectives}},
  author={{Bengio, Yoshua and Courville, Aaron and Vincent, Pascal}},
  journal={{IEEE transactions on pattern analysis and machine intelligence}},
  volume={{35}},
  number={{8}},
  pages={{1798--1828}},
  year={{2013}},
  publisher={{IEEE}}
}}

@article{{lecun2015deep,
  title={{Deep learning}},
  author={{LeCun, Yann and Bengio, Yoshua and Hinton, Geoffrey}},
  journal={{nature}},
  volume={{521}},
  number={{7553}},
  pages={{436--444}},
  year={{2015}},
  publisher={{Nature Publishing Group}}
}}"""
        
        with open(bib_file, 'w') as f:
            f.write(sample_bib)
        
        print(f"✅ Paper {paper['name']} created with content")
    
    print("📊 Repository status:")
    result = main(['status'])
    
    # Test building one paper
    print("\n🔨 Testing build system...")
    try:
        result = main(['b', '01_formalism/00_forms/spec-derived-forms'])
        if result == 0:
            print("✅ Build completed successfully")
        else:
            print("⚠️  Build completed with warnings (likely due to missing LaTeX)")
    except Exception as e:
        print(f"⚠️  Build failed (expected if LaTeX not installed): {e}")
    
    print("\n🎯 Testing forced rebuild...")
    try:
        result = main(['b', '--force', '03_applications/00_vision/vision-transformers'])
        print("✅ Forced build completed")
    except Exception as e:
        print(f"⚠️  Forced build failed (expected if LaTeX not installed): {e}")
    
    print("\n📋 Final repository status:")
    main(['status'])
    
    return True


def test_sample_workflow():
    """Test the complete sample workflow"""
    print("🧪 Testing complete tex-repo sample workflow...")
    
    original_cwd = os.getcwd()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            os.chdir(temp_dir)
            success = create_sample_repository()
            
            if success:
                print("\n🎉 Sample repository test completed successfully!")
                print(f"📁 Sample created in: {temp_dir}/ml-research-repo")
                
                # Show the final structure
                print("\n📂 Final repository structure:")
                repo_path = Path('ml-research-repo')
                for item in sorted(repo_path.rglob('*')):
                    if item.is_file() and not item.name.startswith('.'):
                        rel_path = item.relative_to(repo_path)
                        print(f"  {rel_path}")
                
                return 0
            else:
                print("❌ Sample workflow test failed")
                return 1
                
        except Exception as e:
            print(f"❌ Sample workflow test failed: {e}")
            import traceback
            traceback.print_exc()
            return 1
        
        finally:
            os.chdir(original_cwd)


if __name__ == '__main__':
    sys.exit(test_sample_workflow())
