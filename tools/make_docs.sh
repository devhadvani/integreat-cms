#!/bin/bash

# This script generates the documentation by scanning the source code and extracting definitions and doc strings.

# Configuration
DOCS_DIR="docs"
DOCS_DIST_DIR="${DOCS_DIR}/dist"
DOCS_SRC_DIR="${DOCS_DIR}/src"
APIDOC_SRC_DIR="${DOCS_SRC_DIR}/ref"
APIDOC_EXT_SRC_DIR="${DOCS_SRC_DIR}/ref-ext"

# Import utility functions
# shellcheck source=./tools/_functions.sh
source "$(dirname "${BASH_SOURCE[0]}")/_functions.sh"

require_installed
ensure_not_root

# This function suggests the clean parameter
function suggest_clean_parameter  {
    echo -e "\nIf you think the above error is not your fault, try a clean documentation build with:\n" | print_info
    echo -e "\t${0} --clean\n" | print_bold
}

# Remove stale doc files
if [[ "$*" == *"--clean"* ]] || [[ "$*" == *"--make-clean"* ]]; then
    echo "Removing temporary documentation files." | print_info
    rm -rf "${DOCS_DIST_DIR}" "${APIDOC_SRC_DIR}" "${APIDOC_EXT_SRC_DIR}"
    if [[ "$*" == *"--make-clean"* ]]; then
        echo -e "✔ Cleaned up" | print_success
        exit 0
    fi
elif [[ -z "$CIRCLECI" ]]; then
    # If the script is neither running on CircleCI, nor a clean build and failing anyway, trap to suggest the --clean parameter
    trap 'suggest_clean_parameter' ERR
fi

echo -e "Patching Sphinx templates..." | print_info

THEME_DIR=$(python -c "import os, sphinx_rtd_theme; print(os.path.dirname(sphinx_rtd_theme.__file__))")

# Copy original footer file
cp "${THEME_DIR}/footer.html" "${DOCS_SRC_DIR}/templates"
# Patch footer to add hyperlinks to copyright information
if ! patch "${DOCS_SRC_DIR}/templates/footer.html" "${DOCS_SRC_DIR}/patches/footer.diff"; then
    echo -e "\nThe patch for the footer template could not be applied correctly." | print_error
    echo "Presumably the upstream repository of sphinx_rtd_theme changed." | print_error
    echo "Please adapt ${DOCS_SRC_DIR}/patches/footer.diff to the upstream changes." | print_error
    exit 1
fi

# Copy original breadcrumbs file
cp "${THEME_DIR}/breadcrumbs.html" "${DOCS_SRC_DIR}/templates"
# Patch footer to add hyperlinks to copyright information
if ! patch "${DOCS_SRC_DIR}/templates/breadcrumbs.html" "${DOCS_SRC_DIR}/patches/breadcrumbs.diff"; then
    echo -e "\nThe patch for the breadcrumbs template could not be applied correctly." | print_error
    echo "Presumably the upstream repository of sphinx_rtd_theme changed." | print_error
    echo "Please adapt ${DOCS_SRC_DIR}/patches/breadcrumbs.diff to the upstream changes." | print_error
    exit 1
fi

echo -e "Scanning Python source code and generating reStructuredText files from it..." | print_info

# Generate new .rst files from source code for maximum verbosity
export SPHINX_APIDOC_OPTIONS="members,undoc-members,inherited-members,show-inheritance"
sphinx-apidoc --no-toc --module-first -o "${APIDOC_EXT_SRC_DIR}" "${PACKAGE_DIR}" "${PACKAGE_DIR}/cms/migrations"

# Generate rst files for tests module
sphinx-apidoc --no-toc --module-first -o "${APIDOC_EXT_SRC_DIR}" "tests"

echo -e "Patching reStructuredText files..." | print_info

# Modify .rst files to remove unnecessary submodule- & subpackage-titles
# Example: "integreat_cms.cms.models.push_notifications.push_notification_translation module" becomes "Push Notification Translation"
# At first, the 'find'-command returns all .rst files in the sphinx directory
# The sed pattern replacement is divided into five stages explained below:
find "${APIDOC_EXT_SRC_DIR}" -type f -name "*.rst" -print0 | xargs -0 --no-run-if-empty sed --in-place \
    -e '/Submodules\|Subpackages/{N;d;}' `# Remove Sub-Headings including their following lines` \
    -e 's/\( module\| package\)//' `# Remove module & package strings at the end of headings` \
    -e '/^[^ ]\+$/s/\(.*\.\)\?\([^\.]\+\)/\u\2/' `# Remove module path in headings (separated by dots) and make first letter uppercase` \
    -e '/^[^ ]\+$/s/\\_\([a-z]\)/ \u\1/g' `# Replace \_ with spaces in headings and make following letter uppercase` \
    -e 's/Cms/CMS/g;s/Api/API/g;s/Poi/POI/g;s/Mfa/MFA/g;s/Pdf/PDF/g;s/Xliff1/XLIFF 1.2/g;s/Xliff2/XLIFF 2.0/g;s/Xliff/XLIFF/g;s/Summ Ai/SUMM.AI/g' # Make specific keywords uppercase

# Include _urls in sitemap automodule
# shellcheck disable=SC2251
! grep --recursive --files-without-match ":private-members:" "${APIDOC_EXT_SRC_DIR}/integreat_cms.sitemap.rst" --null | xargs --null --no-run-if-empty sed --in-place '/^\.\. automodule:: integreat_cms.sitemap\.sitemaps/a \ \ \ :private-members:'

# Patch integreat_cms.cms.rst to add the decorated functions
PATCH_STDOUT=$(patch --forward "${APIDOC_EXT_SRC_DIR}/integreat_cms.cms.rst" "${DOCS_SRC_DIR}/patches/cms.diff") && PATCH_STATUS=$? || PATCH_STATUS=$?
# Check if the patch failed and a real error occurred (not only skipping because the patch is already applied)
if [[ "$PATCH_STATUS" -ne 0 ]] && ! echo "$PATCH_STDOUT" | grep --quiet "Reversed (or previously applied) patch detected!  Skipping patch."; then
    echo -e "\nThe patch for integreat_cms.cms.rst could not be applied correctly." | print_error
    echo "Presumably the structure of the cms package changed." | print_error
    echo "Please adapt ${DOCS_SRC_DIR}/patches/cms.diff to the structure changes." | print_error
    exit 1
fi
echo "$PATCH_STDOUT"

# Generate new .rst files from source code for simple version (noindex to prevent double targets for the same source file)
cp -R "${APIDOC_EXT_SRC_DIR}/." "${APIDOC_SRC_DIR}"

# Remove undocumented and inherited members from normal reference and set noindex
find "${APIDOC_SRC_DIR}" -type f -name "*.rst" -print0 | xargs -0 --no-run-if-empty sed --in-place \
    -e '/:undoc-members:/d' `# Remove undoc-members from normal ref` \
    -e '/:inherited-members:/d' `# Remove inherited-members from normal ref` \
    -e '/:show-inheritance:/a \ \ \ :noindex:' # Insert :noindex: after :show-inheritance: option

# Add :noindex: to decorated functions in integreat_cms.cms.rst inserted by the patch
sed --in-place '/\.\. autofunction:: /a \ \ \ \ \ \ :noindex:' "${APIDOC_SRC_DIR}/integreat_cms.cms.rst"

# Set verbose reference as orphans to suppress warnings about toctree
# shellcheck disable=SC2251
! grep --recursive --files-without-match ":orphan:" "${APIDOC_EXT_SRC_DIR}"/*.rst --null | xargs --null --no-run-if-empty sed --in-place '1s/^/:orphan:\n\n/'

# Add release notes to documentation files
RELEASE_NOTES="${DOCS_SRC_DIR}/release-notes.rst"
"${DEV_TOOL_DIR}/make_release_notes.sh" --format=rst --all --output="${RELEASE_NOTES}"

echo -e "Compiling reStructuredText files to HTML documentation..." | print_info

# Compile .rst files to html documentation
sphinx-build -j auto -W --keep-going "${DOCS_SRC_DIR}" "${DOCS_DIST_DIR}"

# Remove temporary release notes file
rm "${RELEASE_NOTES}"

# Check if script is running in CircleCI context
if [[ -n "$CIRCLECI" ]]; then
    # Remove temporary intermediate build files (they should not be committed to gh-pages)
    rm -r "${DOCS_DIST_DIR}/.doctrees"
    rm -r "${DOCS_DIST_DIR}/_sources"
    rm "${DOCS_DIST_DIR}/.buildinfo"
    echo -e "Removed temporary intermediate build files" | print_info
else
    echo -e "✔ Documentation build complete 😻" | print_success
    echo -e "Open the following file in your browser to view the result:\n" | print_info
    echo -e "\tfile://${BASE_DIR}/${DOCS_DIST_DIR}/index.html\n" | print_bold
fi
