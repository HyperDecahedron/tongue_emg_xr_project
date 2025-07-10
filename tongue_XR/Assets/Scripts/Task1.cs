using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using TMPro;

public class Task1 : MonoBehaviour
{
    // Text
    [SerializeField] private TextMeshProUGUI selection_counter;

    // Managers
    [SerializeField] private UDP_Listener udp_listener;
    [SerializeField] private TaskManager taskManager;
    [SerializeField] private GameObject taskParent;

    // Cubes
    [SerializeField] private GameObject cubeLeft;
    [SerializeField] private GameObject cubeFront;
    [SerializeField] private GameObject cubeRight;
    [SerializeField] private Renderer cubePanel;

    // Materials
    [SerializeField] private Material greenMat;
    [SerializeField] private Material yellowMat;
    [SerializeField] private Material redMat;

    private int correct_answers = 0;
    private int total_answers = 0;
    private int selection_count = 0;
    private bool awaitingInput = false;

    private List<int> colours = new List<int> { 1, 2, 3, 2, 3, 1, 1, 3, 2, 1 }; // 1: left (green), 2: front (yellow), 3: right (red)

    private string lastInput = "";
    private int consecutiveCount = 0;
    private int classes_in_a_row = 3;
    private bool taskFinished = false;

    public void StartTask()
    {
        selection_count = 0;
        correct_answers = 0;
        total_answers = 0;
        taskFinished = false;

        udp_listener.OnDataReceived += HandleClassInput;
        StartCoroutine(SelectionLoop());
    }

    public void Hide() => taskParent.SetActive(false);
    public void Show() => taskParent.SetActive(true);

    private IEnumerator SelectionLoop()
    {
        while (selection_count < colours.Count)
        {
            int target = colours[selection_count];

            // Animate panel cube color change
            Material targetMat = GetMaterialFromIndex(target);
            yield return StartCoroutine(AnimatePanelColor(targetMat));
            selection_counter.text = $"{selection_count+1} / 10";

            awaitingInput = true;
            lastInput = "";
            consecutiveCount = 0;

            // Wait for correct input
            yield return new WaitUntil(() => consecutiveCount >= classes_in_a_row || taskFinished);

            if (taskFinished) yield break;

            awaitingInput = false;
            GameObject selectedCube = GetCubeByInput(lastInput);

            if (selectedCube != null)
            {
                StartCoroutine(ElevateCube(selectedCube)); // Visual feedback
            }

            // Check correctness
            int selectedIndex = InputToIndex(lastInput);
            if (selectedIndex == target)
                correct_answers++;

            total_answers++;
            selection_count++;

            yield return new WaitForSeconds(1.5f);
        }

        FinishTask();
    }

    private void HandleClassInput(UDP_Listener.UdpData data)
    {
        if (!awaitingInput || taskFinished) return;

        string input = data.Class;

        if (input != "l" && input != "f" && input != "r") return;

        if (input == lastInput)
        {
            consecutiveCount++;
        }
        else
        {
            lastInput = input;
            consecutiveCount = 1;
        }
    }

    private GameObject GetCubeByInput(string input)
    {
        switch (input)
        {
            case "l": return cubeLeft;
            case "f": return cubeFront;
            case "r": return cubeRight;
            default: return null;
        }
    }

    private int InputToIndex(string input)
    {
        switch (input)
        {
            case "l": return 1;
            case "f": return 2;
            case "r": return 3;
            default: return 0;
        }
    }

    // Smoothly elevates the selected cube for visual feedback
    private IEnumerator ElevateCube(GameObject cube)
    {
        Vector3 originalPos = cube.transform.position;
        Vector3 targetPos = originalPos + new Vector3(0, 0.1f, 0);
        float duration = 0.3f;
        float elapsed = 0f;

        while (elapsed < duration)
        {
            cube.transform.position = Vector3.Lerp(originalPos, targetPos, elapsed / duration);
            elapsed += Time.deltaTime;
            yield return null;
        }

        cube.transform.position = targetPos;

        yield return new WaitForSeconds(0.3f);

        elapsed = 0f;
        while (elapsed < duration)
        {
            cube.transform.position = Vector3.Lerp(targetPos, originalPos, elapsed / duration);
            elapsed += Time.deltaTime;
            yield return null;
        }

        cube.transform.position = originalPos;
    }

    // Shrinks, changes material, then expands the panel cube for color transition feedback
    private IEnumerator AnimatePanelColor(Material newMat)
    {
        Vector3 originalScale = cubePanel.transform.localScale;
        Vector3 shrunkenScale = originalScale * 0.5f;
        float duration = 0.2f;
        float elapsed = 0f;

        // Shrink
        while (elapsed < duration)
        {
            cubePanel.transform.localScale = Vector3.Lerp(originalScale, shrunkenScale, elapsed / duration);
            elapsed += Time.deltaTime;
            yield return null;
        }
        cubePanel.transform.localScale = shrunkenScale;

        // Change material
        cubePanel.material = newMat;

        // Expand back
        elapsed = 0f;
        while (elapsed < duration)
        {
            cubePanel.transform.localScale = Vector3.Lerp(shrunkenScale, originalScale, elapsed / duration);
            elapsed += Time.deltaTime;
            yield return null;
        }
        cubePanel.transform.localScale = originalScale;
    }

    private Material GetMaterialFromIndex(int index)
    {
        switch (index)
        {
            case 1: return greenMat;
            case 2: return yellowMat;
            case 3: return redMat;
            default: return null;
        }
    }

    public void FinishTask()
    {
        taskFinished = true;
        Debug.Log($"Finished Task: Correct Answers = {correct_answers}, Total Answers = {total_answers}");

        udp_listener.OnDataReceived -= HandleClassInput;
        taskManager.IntermediatePanel();
        taskParent.SetActive(false);
        this.gameObject.SetActive(false);
    }
}
